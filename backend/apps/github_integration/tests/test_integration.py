from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import Client as HttpClient
from django.test import RequestFactory, TestCase, override_settings
from ninja.errors import HttpError

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.github_integration.client import GitHubClient, GitHubError, app_token
from apps.github_integration.models import (
    Delivery,
    Installation,
    Item,
    Preference,
    Repository,
    WorkflowAction,
)
from apps.github_integration.ninja.views import (
    DispatchIn,
    dispatch,
    items,
    jobs,
    logs,
    options,
    repositories,
    rerun,
)
from apps.github_integration.services import (
    import_repository,
    save_item,
    sync_installation,
    sync_repository,
)
from apps.github_integration.tasks import process_delivery
from apps.infrastructure.models import InfrastructureResource, SourceRepository
from authentication.models import User


class GitHubTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="github@example.com",
            password="test-password",
            first_name="GitHub",
            last_name="User",
            is_staff=True,
        )
        permissions = Permission.objects.filter(
            content_type__app_label__in=["github_integration", "infrastructure"],
            codename__in=["view_repository", "view_infrastructureresource"],
        )
        self.user.user_permissions.add(*permissions)
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(name="A", email="a@example.com")
        self.client_b = Client.objects.create(name="B", email="b@example.com")
        profile = StaffAccessProfile.objects.create(user=self.user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)
        self.installation = Installation.objects.create(
            github_id=123, account="adb", enabled=True, client=self.client_a
        )
        self.repository = import_repository(self.installation, self.repo_data())
        self.other = import_repository(
            Installation.objects.create(
                github_id=456, account="other", enabled=True, client=self.client_b
            ),
            self.repo_data(2),
        )

    def repo_data(self, github_id: int = 1) -> dict[str, Any]:
        return {
            "id": github_id,
            "full_name": f"adb/repo{github_id}",
            "name": f"repo{github_id}",
            "html_url": f"https://github.com/adb/repo{github_id}",
            "owner": {"login": "adb"},
            "default_branch": "main",
        }

    def request(self) -> HttpRequest:
        request = self.factory.get("/")
        request.user = self.user
        return request

    def grant(self, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label="github_integration", codename=codename)
        )
        self.user = User.objects.get(pk=self.user.pk)

    @override_settings(
        GITHUB_APP_ID="123", GITHUB_WEBHOOK_SECRET="webhook-secret", GITHUB_APP_SLUG="adb-app"
    )
    def test_options_uses_environment_key_without_exposing_it(self) -> None:
        for pem, configured in (("", False), ("private-key-secret", True)):
            with override_settings(GITHUB_APP_PRIVATE_KEY=pem):
                result = options(self.request())
            self.assertEqual(result["configured"], configured)
            self.assertNotIn("private-key-secret", json.dumps(result))

    def item(
        self,
        repository: Repository | None = None,
        kind: str = "pull_request",
        login: str = "adam",
        **extra: Any,
    ) -> Item:
        return save_item(
            repository or self.repository,
            kind,
            {
                "id": 500,
                "number": 2,
                "title": "Fix",
                "user": {"login": login, "type": "Bot" if login.endswith("[bot]") else "User"},
                "state": "open",
                **extra,
            },
        )

    def test_http_dashboard_uses_existing_session_and_scope(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get("/api/admin/github/repositories")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 1)

    def test_http_mutations_require_csrf_even_with_valid_session(self) -> None:
        client = HttpClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.put(
            "/api/admin/github/preference",
            data=json.dumps({"username": "adam"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Preference.objects.exists())
        client.get("/api/csrf")
        token = client.cookies["csrftoken"].value
        response = client.put(
            "/api/admin/github/preference",
            data=json.dumps({"username": "adam"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Preference.objects.get().username, "adam")

    def test_repositories_are_scoped_and_disabled_installations_hidden(self) -> None:
        self.assertEqual(
            [row["id"] for row in repositories(self.request())["rows"]], [self.repository.pk]
        )
        self.installation.enabled = False
        self.installation.save()
        self.assertEqual(repositories(self.request())["total"], 0)

    def test_missing_capability_is_denied(self) -> None:
        self.user.user_permissions.clear()
        self.user = User.objects.get(pk=self.user.pk)
        with self.assertRaises(HttpError) as error:
            repositories(self.request())
        self.assertEqual(error.exception.status_code, 403)

    def test_my_work_and_dependabot_filters(self) -> None:
        Preference.objects.create(user=self.user, username="adam")
        self.item(assignees=[{"login": "adam"}], login="colleague")
        bot = self.item(kind="issue", login="dependabot[bot]")
        self.item(self.other, login="adam")
        self.assertEqual(items(self.request())["total"], 1)
        self.assertEqual(items(self.request(), kind="issue")["total"], 0)
        self.assertEqual(
            items(self.request(), kind="issue", view="dependabot")["rows"][0]["id"], bot.pk
        )

    def test_review_requests_and_empty_username(self) -> None:
        self.item(login="colleague", requested_reviewers=[{"login": "adam"}])
        self.assertEqual(items(self.request())["total"], 0)
        Preference.objects.create(user=self.user, username="adam")
        self.assertEqual(items(self.request())["total"], 1)

    def test_import_reuses_existing_manual_inventory(self) -> None:
        resource = InfrastructureResource.objects.create(
            name="Manual",
            resource_type="source_repository",
            ownership_type="client",
            client=self.client_a,
        )
        source = SourceRepository.objects.create(
            resource=resource, repository_name="repo3", web_url="https://github.com/adb/repo3"
        )
        imported = import_repository(self.installation, self.repo_data(3))
        self.assertEqual(imported.source_id, source.pk)
        self.assertEqual(import_repository(self.installation, self.repo_data(3)).pk, imported.pk)

    def test_repository_cannot_move_between_owners(self) -> None:
        from apps.github_integration.client import GitHubError

        with self.assertRaises(GitHubError):
            import_repository(self.other.installation, self.repo_data())

    def test_assignment_username_matching_ignores_case(self) -> None:
        Preference.objects.create(user=self.user, username="Adam")
        self.item(login="colleague", assignees=[{"login": "ADAM"}])
        self.assertEqual(items(self.request())["total"], 1)

    def test_new_repository_with_reused_url_has_separate_remote_identity(self) -> None:
        data = self.repo_data()
        data["id"] = 77
        recreated = import_repository(self.installation, data)
        self.assertNotEqual(recreated.source_id, self.repository.source_id)

    def test_non_github_provider_ids_do_not_collide(self) -> None:
        resource = InfrastructureResource.objects.create(
            name="GitLab",
            resource_type="source_repository",
            ownership_type="client",
            client=self.client_a,
        )
        source = SourceRepository.objects.create(
            resource=resource,
            repository_name="repo3",
            provider_repository_id="3",
            web_url="https://gitlab.com/adb/repo3",
        )
        imported = import_repository(self.installation, self.repo_data(3))
        self.assertNotEqual(imported.source_id, source.pk)

    def test_stale_remote_snapshot_does_not_overwrite_newer_state(self) -> None:
        self.item(state="closed", updated_at="2026-10-05T12:00:00Z")
        self.item(state="open", updated_at="2026-10-04T12:00:00Z")
        self.assertEqual(Item.objects.get().state, "closed")

    @patch("apps.github_integration.services.sync_repository")
    @patch.object(GitHubClient, "pages")
    def test_one_repository_failure_does_not_block_other_imports(
        self, pages: Any, sync: Any
    ) -> None:
        from apps.github_integration.client import GitHubError

        pages.return_value = [self.repo_data(), self.repo_data(3)]
        sync.side_effect = [GitHubError("GitHub returned HTTP 403."), None]
        with self.assertRaises(GitHubError):
            sync_installation(self.installation.pk)
        self.assertEqual(Repository.objects.filter(installation=self.installation).count(), 2)
        self.assertEqual(sync.call_count, 2)
        self.repository.refresh_from_db()
        self.assertIn("403", self.repository.sync_error)

    @patch.object(GitHubClient, "pages")
    @patch.object(GitHubClient, "request")
    def test_disabled_issues_do_not_block_workflows(self, remote: Any, pages: Any) -> None:
        pages.return_value = []
        remote.return_value = {"workflow_runs": []}
        sync_repository(self.repository, has_issues=False)
        self.assertEqual(pages.call_count, 2)
        self.assertFalse(any("/issues" in call.args[0] for call in pages.call_args_list))

    @patch("apps.github_integration.ninja.views.remote")
    def test_dispatch_permission_and_scope(self, remote: Any) -> None:
        self.item(kind="workflow", state="active")
        with self.assertRaises(HttpError) as error:
            dispatch(self.request(), self.repository.pk, 500, DispatchIn(ref="main"))
        self.assertEqual(error.exception.status_code, 403)
        remote.assert_not_called()
        self.grant("trigger_workflow")
        with self.assertRaises(HttpError) as error:
            dispatch(self.request(), self.other.pk, 500, DispatchIn(ref="main"))
        self.assertEqual(error.exception.status_code, 404)
        dispatch(
            self.request(),
            self.repository.pk,
            500,
            DispatchIn(ref="main", inputs={"secret": "not-stored"}),
        )
        self.assertEqual(WorkflowAction.objects.get().action, "dispatch")
        self.assertNotIn("not-stored", str(WorkflowAction.objects.values().get()))

    @patch("apps.github_integration.ninja.views.remote")
    def test_only_failed_runs_can_rerun(self, remote: Any) -> None:
        self.grant("trigger_workflow")
        self.item(kind="run", status="completed", conclusion="success")
        with self.assertRaises(HttpError):
            rerun(self.request(), self.repository.pk, 500)
        remote.assert_not_called()
        self.item(kind="run", status="completed", conclusion="failure")
        self.assertTrue(rerun(self.request(), self.repository.pk, 500)["started"])

    @patch("apps.github_integration.ninja.views.remote")
    def test_jobs_are_paginated_and_scope_checked(self, remote: Any) -> None:
        self.item(kind="run", status="completed")
        remote.return_value = {"total_count": 60, "jobs": []}
        result = jobs(self.request(), self.repository.pk, 500, page=2)
        self.assertEqual(result["total"], 60)
        self.assertIn("per_page=25&page=2", remote.call_args.args[2])
        remote.reset_mock()
        with self.assertRaises(HttpError):
            jobs(self.request(), self.other.pk, 500)
        remote.assert_not_called()

    @patch("apps.github_integration.ninja.views.remote")
    @patch.object(GitHubClient, "job_logs")
    def test_logs_require_permission_and_job_membership(self, job_logs: Any, remote: Any) -> None:
        self.item(kind="run", status="completed")
        with self.assertRaises(HttpError):
            logs(self.request(), self.repository.pk, 500, 700)
        job_logs.assert_not_called()
        self.grant("view_workflow_logs")
        remote.return_value = {"run_id": 999}
        with self.assertRaises(HttpError) as error:
            logs(self.request(), self.repository.pk, 500, 700)
        self.assertEqual(error.exception.status_code, 404)
        job_logs.assert_not_called()
        remote.return_value = {"run_id": 500}
        job_logs.return_value = ("safe output", False)
        self.assertEqual(logs(self.request(), self.repository.pk, 500, 700)["text"], "safe output")
        self.assertNotIn("safe output", str(WorkflowAction.objects.values().get()))

    @patch.object(GitHubClient, "pages")
    @patch.object(GitHubClient, "request")
    def test_sync_preserves_merged_history(self, remote: Any, pages: Any) -> None:
        item = self.item(merged_at="2026-10-01T12:00:00Z")
        pages.return_value = []
        remote.return_value = {"workflow_runs": []}
        sync_repository(self.repository)
        item.refresh_from_db()
        self.assertEqual(item.state, "merged")


@override_settings(GITHUB_WEBHOOK_SECRET="test-webhook")
class WebhookTests(TestCase):
    def send(
        self,
        payload: dict[str, Any],
        event: str = "installation",
        delivery: str = "delivery-1",
        valid: bool = True,
    ) -> Any:
        body = json.dumps(payload).encode()
        signature = "sha256=" + hmac.new(b"test-webhook", body, hashlib.sha256).hexdigest()
        return self.client.post(
            "/api/integrations/github/webhook",
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=signature if valid else "invalid",
            HTTP_X_GITHUB_EVENT=event,
            HTTP_X_GITHUB_DELIVERY=delivery,
        )

    @patch("apps.github_integration.webhooks.enqueue")
    def test_signature_required(self, enqueue: Any) -> None:
        self.assertEqual(self.send({}, valid=False).status_code, 403)
        self.assertFalse(Delivery.objects.exists())
        enqueue.assert_not_called()

    @patch("apps.github_integration.webhooks.enqueue")
    def test_idempotent_sanitised_delivery_creates_pending_installation(self, enqueue: Any) -> None:
        payload = {
            "action": "created",
            "installation": {"id": 123, "account": {"login": "adb"}},
            "private_body": "never store this",
        }
        self.assertEqual(self.send(payload).status_code, 202)
        self.assertEqual(self.send(payload).status_code, 200)
        self.assertEqual(Delivery.objects.count(), 1)
        enqueue.assert_called_once()
        delivery = Delivery.objects.get()
        self.assertNotIn("never store this", json.dumps(delivery.payload))
        process_delivery(delivery.pk)
        self.assertFalse(Installation.objects.get().enabled)
        delivery.refresh_from_db()
        self.assertIsNotNone(delivery.processed_at)

    @patch("apps.github_integration.webhooks.enqueue")
    def test_suspension_revokes_immediately(self, enqueue: Any) -> None:
        installation = Installation.objects.create(github_id=123, account="adb", enabled=True)
        self.send({"action": "suspend", "installation": {"id": 123}})
        installation.refresh_from_db()
        self.assertFalse(installation.enabled)

    @override_settings(GITHUB_WEBHOOK_SECRET="")
    def test_unconfigured_returns_503(self) -> None:
        self.assertEqual(self.send({}).status_code, 503)

    @patch("apps.github_integration.tasks.GitHubClient.request")
    @patch("apps.github_integration.webhooks.enqueue")
    def test_update_fetches_current_state_instead_of_stale_payload(
        self, enqueue: Any, remote: Any
    ) -> None:
        installation = Installation.objects.create(github_id=123, account="adb", enabled=True)
        repository = import_repository(
            installation,
            {
                "id": 1,
                "full_name": "adb/repo",
                "name": "repo",
                "html_url": "https://github.com/adb/repo",
                "owner": {"login": "adb"},
            },
        )
        remote.return_value = {"id": 5, "number": 2, "title": "Current", "state": "closed"}
        self.send(
            {
                "installation": {"id": 123},
                "repository": {"id": 1},
                "issue": {"id": 5, "number": 2, "state": "open"},
            },
            event="issues",
        )
        process_delivery(Delivery.objects.get().pk)
        self.assertEqual(Item.objects.get(repository=repository).state, "closed")


class ClientTests(TestCase):
    @override_settings(GITHUB_APP_ID="123", CREDENTIAL_ENCRYPTION_KEYS="")
    def test_jwt_is_signed_from_environment_without_database_or_vault(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        for key_format, escaped in (
            (serialization.PrivateFormat.PKCS8, False),
            (serialization.PrivateFormat.TraditionalOpenSSL, True),
        ):
            pem = key.private_bytes(
                serialization.Encoding.PEM,
                key_format,
                serialization.NoEncryption(),
            ).decode()
            with (
                self.subTest(key_format=key_format, escaped=escaped),
                override_settings(
                    GITHUB_APP_PRIVATE_KEY=pem.replace("\n", "\\n") if escaped else pem
                ),
                self.assertNumQueries(0),
            ):
                token = app_token()
                header, claims, signature = token.split(".")
                decoded = json.loads(base64.urlsafe_b64decode(claims + "=" * (-len(claims) % 4)))
                self.assertEqual(decoded["iss"], "123")
                self.assertEqual(decoded["exp"] - decoded["iat"], 600)
                key.public_key().verify(
                    base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)),
                    f"{header}.{claims}".encode(),
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )

    def test_missing_configuration_is_reported_safely(self) -> None:
        for app_id, pem in (("", "secret-value"), ("123", "")):
            with (
                self.subTest(app_id=app_id),
                override_settings(GITHUB_APP_ID=app_id, GITHUB_APP_PRIVATE_KEY=pem),
                self.assertRaisesMessage(
                    GitHubError, "Configure GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY"
                ),
            ):
                app_token()

    @override_settings(GITHUB_APP_ID="123")
    def test_invalid_and_non_rsa_keys_do_not_expose_key_material(self) -> None:
        key = ec.generate_private_key(ec.SECP256R1())
        for pem in (
            "invalid-private-key-secret",
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode(),
        ):
            with override_settings(GITHUB_APP_PRIVATE_KEY=pem):
                with self.assertRaises(GitHubError) as error:
                    app_token()
                self.assertEqual(
                    str(error.exception),
                    "GITHUB_APP_PRIVATE_KEY must contain a valid unencrypted RSA PEM key.",
                )
                self.assertNotIn(pem, str(error.exception))

    @patch.object(GitHubClient, "request")
    def test_pagination_fetches_all_pages(self, request: Any) -> None:
        request.side_effect = [[{"id": number} for number in range(100)], [{"id": 100}]]
        self.assertEqual(len(GitHubClient(1).pages("/installation/repositories")), 101)
        self.assertIn("page=2", request.call_args.args[1])
