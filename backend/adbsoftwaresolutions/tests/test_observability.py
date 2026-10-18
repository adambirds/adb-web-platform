import json
import logging
import os
import sys
from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings

from adbsoftwaresolutions.logs import JsonFormatter, logging_config

LOCAL_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "session": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@override_settings(CACHES=LOCAL_CACHES)
class HealthzTests(TestCase):
    def test_ok(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "checks": {
                    "database": {"ok": True},
                    "cache:default": {"ok": True},
                    "cache:session": {"ok": True},
                },
            },
        )

    @override_settings(ALLOWED_HOSTS=["api.adbsoftwaresolutions.co.uk"], SECURE_SSL_REDIRECT=True)
    def test_answers_the_container_health_check(self) -> None:
        # Docker calls http://127.0.0.1:8000/healthz: not an allowed host, not HTTPS.
        for path in ("/healthz", "/metrics"):
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST="127.0.0.1:8000")
                self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/", HTTP_HOST="127.0.0.1:8000")
        self.assertEqual(response.status_code, 400)

    def test_database_down_is_degraded(self) -> None:
        with mock.patch(
            "adbsoftwaresolutions.health._database",
            side_effect=OperationalError("no route to host"),
        ):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["checks"]["database"], {"ok": False, "error": "OperationalError"})

    def test_cache_down_is_degraded(self) -> None:
        with mock.patch(
            "django.core.cache.backends.locmem.LocMemCache.get", side_effect=ConnectionError
        ):
            body = self.client.get("/healthz").json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["checks"]["cache:session"], {"ok": False, "error": "ConnectionError"})
        self.assertTrue(body["checks"]["database"]["ok"])


@override_settings(CACHES=LOCAL_CACHES)
class MetricsTests(TestCase):
    def test_prometheus_text_with_request_metrics(self) -> None:
        self.client.get("/admin/login/")
        self.client.get("/healthz")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        text = response.content.decode()
        self.assertIn(
            'django_http_responses_total_by_status_view_method_total{method="GET",status="200",'
            'view="admin:login"}',
            text,
        )
        # Health checks and scrapes are not counted.
        self.assertNotIn('view="<unnamed view>"', text)


class JsonFormatterTests(SimpleTestCase):
    def record(self, **kwargs: object) -> logging.LogRecord:
        record = logging.LogRecord(
            "adbsoftwaresolutions.test", logging.WARNING, __file__, 1, "%s left", ("2",), None
        )
        record.created = 1767323045.5
        record.__dict__.update(kwargs)
        return record

    def test_fields(self) -> None:
        entry = json.loads(JsonFormatter(service="adb-web-platform-backend").format(self.record()))
        self.assertEqual(
            entry,
            {
                "time": "2026-01-02T03:04:05.500+00:00",
                "level": "warning",
                "logger": "adbsoftwaresolutions.test",
                "message": "2 left",
                "service": "adb-web-platform-backend",
            },
        )

    def test_exception_and_extra(self) -> None:
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
        entry = json.loads(JsonFormatter().format(self.record(exc_info=exc_info, user_id=7)))
        self.assertIn("ValueError: boom", entry["exception"])
        self.assertEqual(entry["user_id"], 7)

    def test_service_from_environment(self) -> None:
        with mock.patch.dict(os.environ, {"SERVICE_NAME": "adb-web-platform-celery-worker"}):
            self.assertEqual(JsonFormatter().service, "adb-web-platform-celery-worker")

    def test_log_format_switch(self) -> None:
        with mock.patch.dict(os.environ, {"LOG_FORMAT": "json"}):
            self.assertEqual(logging_config()["handlers"]["console"]["formatter"], "json")
        with mock.patch.dict(os.environ, {"LOG_FORMAT": ""}):
            self.assertEqual(logging_config()["handlers"]["console"]["formatter"], "text")


class OAuthCallbackLoggingTests(SimpleTestCase):
    def test_access_log_redaction_preserves_uvicorn_argument_contract(self) -> None:
        from adbsoftwaresolutions.logs import OAuthCallbackLogFilter

        record = logging.LogRecord(
            "uvicorn.access",
            logging.INFO,
            __file__,
            1,
            '%s - "%s %s HTTP/%s" %d',
            (
                "127.0.0.1",
                "GET",
                "/api/analytics/oauth/callback?code=private-code&state=private-state",
                "1.1",
                302,
            ),
            None,
        )
        self.assertTrue(OAuthCallbackLogFilter().filter(record))
        assert isinstance(record.args, tuple)
        self.assertEqual(len(record.args), 5)
        self.assertIn("/api/analytics/oauth/callback?[redacted]", record.getMessage())
        self.assertNotIn("private-code", record.getMessage())
        self.assertNotIn("private-state", record.getMessage())

    def test_json_logging_redacts_callback_urls_in_messages_and_extra(self) -> None:
        url = "/api/analytics/oauth/callback?code=private-code&state=private-state"
        record = logging.LogRecord(
            "django.request", logging.WARNING, __file__, 1, "Callback %s", (url,), None
        )
        record.__dict__["request_path"] = url
        rendered = JsonFormatter().format(record)
        self.assertNotIn("private-code", rendered)
        self.assertNotIn("private-state", rendered)
        self.assertIn("[redacted]", rendered)
