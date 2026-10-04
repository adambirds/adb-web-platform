from django.test import SimpleTestCase

from adbsoftwaresolutions.celery import app


class CeleryTaskDiscoveryTests(SimpleTestCase):
    def test_discovery_registers_platform_tasks_without_legacy_dependencies(self) -> None:
        app.loader.import_default_modules()

        for schedule in app.conf.beat_schedule.values():
            self.assertIn(schedule["task"], app.tasks)
        self.assertIn("ticketing.deliver_ticket_reply", app.tasks)
        self.assertFalse(any(name.startswith("authentication.tasks.") for name in app.tasks))


class RedisSettingsTests(SimpleTestCase):
    def test_redis_settings_use_separate_environment_urls(self) -> None:
        import runpy
        from pathlib import Path
        from unittest.mock import patch

        urls = {
            "CELERY_BROKER_URL": "redis://broker-test:6379/3",
            "CELERY_RESULT_BACKEND": "redis://broker-test:6379/4",
            "CACHE_BACKEND_URL": "redis://cache-test:6379/5",
            "SESSION_BACKEND_URL": "redis://session-test:6379/6",
        }
        with patch.dict("os.environ", urls):
            config = runpy.run_path(str(Path(__file__).resolve().parents[1] / "settings.py"))

        self.assertEqual(config["CELERY_BROKER_URL"], urls["CELERY_BROKER_URL"])
        self.assertEqual(config["CELERY_RESULT_BACKEND"], urls["CELERY_RESULT_BACKEND"])
        self.assertEqual(config["CACHES"]["default"]["LOCATION"], urls["CACHE_BACKEND_URL"])
        self.assertEqual(config["CACHES"]["session"]["LOCATION"], urls["SESSION_BACKEND_URL"])
        self.assertEqual(config["SESSION_CACHE_ALIAS"], "session")
        self.assertEqual(config["CELERY_TASK_DEFAULT_QUEUE"], "general")
