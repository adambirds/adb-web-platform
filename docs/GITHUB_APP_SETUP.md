# GitHub dashboard and App setup

The internal dashboard is `/admin/github`. Django owns its data, permissions,
Client/Internal scopes, App authentication and workflow actions. It supports any
number of organisation and personal-account installations of one GitHub App.

## Register and install the App

1. Register **one** GitHub App under an account you administer:
   [register under adb-software-solutions](https://github.com/organizations/adb-software-solutions/settings/apps/new)
   or [register under your personal account](https://github.com/settings/apps/new).
   Allow installation on any account so it can be installed on all your
   organisations and personal account. See GitHub's
   [registration instructions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app).
2. Set its webhook URL to the publicly reachable Django endpoint
   `https://<backend-host>/api/integrations/github/webhook`. Enable webhooks and
   choose a strong webhook secret. Open your registered App from
   [adb-software-solutions App settings](https://github.com/organizations/adb-software-solutions/settings/apps)
   or [personal App settings](https://github.com/settings/apps), depending on
   where you registered it. These settings also contain the App ID, permissions,
   event subscriptions and private keys used in the following steps.
   Local development needs an HTTPS tunnel to
   Django; GitHub cannot call `localhost` directly.
3. In your App's **Permissions & events** settings, grant these repository
   permissions. GitHub's [App settings instructions](https://docs.github.com/en/apps/maintaining-github-apps/modifying-a-github-app-registration)
   explain where to change them:

    | Permission    | Access | Purpose                                                   |
    | ------------- | ------ | --------------------------------------------------------- |
    | Metadata      | Read   | Repository identity and installation inventory            |
    | Contents      | Read   | Push events to refresh workflow definitions               |
    | Issues        | Read   | Issue state, authors and assignments                      |
    | Pull requests | Read   | PR state and requested reviewers                          |
    | Actions       | Write  | Workflows, runs, job logs, dispatch and failed-job reruns |

4. Subscribe to `repository`, `issues`, `pull_request`, `push`, `workflow_run`
   and `workflow_job`. Installation lifecycle and repository-access changes are
   delivered to the App as installation events.
5. In your App's **General** settings, find **Private keys** and select
   **Generate a private key**. See GitHub's
   [private-key instructions](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps). Store the complete unencrypted RSA PEM in Infisical as
   `GITHUB_APP_PRIVATE_KEY` and inject it directly into backend environments.
   No Internal Vault credential, credential ID or bootstrap command is required.
   Do not put the key in Git or expose it through the dashboard or frontend
   environment. Multiline PEM and literal `\n` escapes are supported.
6. Configure these variables for Django and every Celery worker/Beat process,
   then restart the processes:

    ```dotenv
    GITHUB_APP_ID=<numeric App ID>
    GITHUB_APP_SLUG=<App slug>
    GITHUB_APP_PRIVATE_KEY=<complete GitHub-generated RSA PEM>
    GITHUB_WEBHOOK_SECRET=<same secret configured in GitHub>
    ```

    To rotate the signing key, generate a replacement in GitHub, update Infisical
    and redeploy the API, all workers and Beat before deleting the old GitHub key.
    Signing reads process configuration directly and does not copy keys into
    application records.

7. Apply Django migrations and run Celery workers and Celery Beat. In development
   the backend environment comes from `.devcontainer/.env` via Compose's
   `env_file`; rebuild/recreate the container after changing it.
8. Install the App on `adb-software-solutions`, `adb-web-designs`, `VastDesk`,
   `vanderheim-village`, `adambirds`, `adb-technology` and `switchonyourcode`.
   Select all repositories if newly created repositories should join automatically.
   Organisation administrators may need to approve an installation. From your
   registered App's settings, select **Install App**, then choose each account;
   see [installing your own App](https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app).
   Use the account links below to review installations and repository access.
9. Open **GitHub → Connections**. Signed installation events create pending
   connections. Choose **Choose ownership and approve**, select Internal or the
   correct Client, then **Connect and synchronise**. You can also enter the numeric
   installation ID from the GitHub installation settings URL manually.
   Approval validates the installation against the configured App before import.

App registration and installation are external setup steps. No account is
connected merely because its name appears in this guide.

## Direct GitHub settings links

Create the App once, then install that same App on every required account.
The App registration settings manage its webhook, signing keys, permissions and
subscriptions. The installation settings manage its access to an account's
repositories and provide the installation ID when you click **Configure**.

| Account                | App registration settings                                                           | Installed Apps / repository access                                                              |
| ---------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| adb-software-solutions | [Owned Apps](https://github.com/organizations/adb-software-solutions/settings/apps) | [Installations](https://github.com/organizations/adb-software-solutions/settings/installations) |
| adb-web-designs        | [Owned Apps](https://github.com/organizations/adb-web-designs/settings/apps)        | [Installations](https://github.com/organizations/adb-web-designs/settings/installations)        |
| VastDesk               | [Owned Apps](https://github.com/organizations/VastDesk/settings/apps)               | [Installations](https://github.com/organizations/VastDesk/settings/installations)               |
| vanderheim-village     | [Owned Apps](https://github.com/organizations/vanderheim-village/settings/apps)     | [Installations](https://github.com/organizations/vanderheim-village/settings/installations)     |
| adambirds (personal)   | [Owned Apps](https://github.com/settings/apps)                                      | [Installations](https://github.com/settings/installations)                                      |
| adb-technology         | [Owned Apps](https://github.com/organizations/adb-technology/settings/apps)         | [Installations](https://github.com/organizations/adb-technology/settings/installations)         |
| switchonyourcode       | [Owned Apps](https://github.com/organizations/switchonyourcode/settings/apps)       | [Installations](https://github.com/organizations/switchonyourcode/settings/installations)       |

Personal settings links open the currently signed-in GitHub account; sign in as
`adambirds` to configure that account. Organisation settings require the relevant
organisation access.

Once you have an App slug, its direct installation URL is
`https://github.com/apps/YOUR-APP-SLUG/installations/new`. Replace
`YOUR-APP-SLUG` with your actual slug; the platform's **Install GitHub App** button
uses this URL automatically after you configure `GITHUB_APP_SLUG`.

To inspect failed webhook deliveries, open the registered App from its **Owned
Apps** link, then **Advanced → Recent Deliveries**. GitHub provides
[delivery inspection instructions](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/viewing-webhook-deliveries)
and [redelivery instructions](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks).

## Permissions and ownership

Use Users & Access to grant `github_integration.view_repository` together with
`infrastructure.view_infrastructureresource`. Repository visibility additionally
uses the existing Client scope layer; inaccessible repositories return 404.

The following independent capabilities apply in addition to viewing:

- `github_integration.manage_github`: approve installations and request syncs;
- `github_integration.trigger_workflow`: start workflows and rerun failed jobs;
- `github_integration.view_workflow_logs`: retrieve job logs on demand.

Connection approval also requires `infrastructure.add_infrastructureresource`
and `infrastructure.add_sourcerepository`, because it imports inventory records.
Ownership cannot change after repositories have been imported. Configure each
installation for one Client or Internal context. GitHub access never bypasses
platform scopes. Suspending or deleting an installation hides its GitHub records
immediately; removing repository access hides that repository immediately.

## What synchronises

Initial/manual sync imports all accessible repositories, open issues and PRs,
workflow definitions and the latest 30 workflow runs per repository. Subsequent
webhooks retrieve current GitHub state, rather than trusting stale event content.
Closed/merged work received after connection remains available in synced history.
This is not a complete import of every historical closed issue or run.

Repository imports reuse matching infrastructure SourceRepository records within
the same ownership context; they do not create separate application repositories.
An application's **Linked repositories** section records its role and optional
monorepo folder path against that shared repository record.

"My work" uses your saved GitHub username and matches authorship, assignment or
requested review. It excludes bots; Dependabot has its own filter. The username
is a display preference, not proof of GitHub identity or an access grant.

Webhooks drive updates automatically. The shared [live updates stream](LIVE_UPDATES_ARCHITECTURE.md)
refreshes visible GitHub screens after processing finishes. Delivery, worker scheduling and API availability affect latency; updates
are normally visible within seconds, rather than a guaranteed instant.

Signed deliveries are deduplicated by delivery ID and stored before queueing.
Beat retries unprocessed deliveries every minute if the broker or GitHub is
unavailable. Errors shown in Connections omit remote response bodies and tokens.
Use **Synchronise now** to repair missed events; check GitHub's App webhook
recent-deliveries page and redeliver failures after fixing configuration.

## Actions and logs

Starting a workflow requires `workflow_dispatch` in its GitHub workflow file and
a valid branch/tag. Supply any declared inputs as a JSON object of text values.
GitHub validates workflow-specific input requirements. The UI requests confirmation
before a dispatch or failed-job rerun. Failed-job reruns require a completed run
with failure or timeout; successful runs are not offered for rerun.

Jobs load on demand from GitHub. Logs are retrieved only after checking repository
scope, log permission and job membership of the selected run. Only the first
256 KB is shown; use the job's GitHub link for the full output. Tokens, private
keys and logs are never persisted in integration records. Trigger and log-access
audit records include the actor and GitHub identifier, without log bodies or
workflow input values. Installation tokens expire in a short-lived server cache.

## Code map

- `backend/apps/github_integration/client.py`: App JWT, installation tokens and REST transport;
- `services.py`: native repository import and safe work-item projections;
- `webhooks.py`: signature verification, durable routing metadata and revocation;
- `tasks.py`: Celery synchronisation and delivery recovery;
- `ninja/views.py`: scoped dashboard APIs and permissioned workflow/log endpoints;
- `sites/adb-software-solutions/src/app/(admin)/admin/github/`: dashboard and account/action UI.

Official references: [App JWT authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app),
[webhook events](https://docs.github.com/en/webhooks/webhook-events-and-payloads),
[workflow dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event),
[failed-job reruns](https://docs.github.com/en/rest/actions/workflow-runs#re-run-failed-jobs-from-a-workflow-run)
and [job logs](https://docs.github.com/en/rest/actions/workflow-jobs#download-job-logs-for-a-workflow-run).
