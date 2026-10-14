# GitHub dashboard and App setup

The internal dashboard is `/admin/github`. Django owns its data, permissions,
Client/Internal scopes, App authentication and workflow actions. It supports any
number of organisation and personal-account installations of one GitHub App.

## Before filling in the form

Use **one GitHub App** for the organisations and personal account listed below.
Register it under `adb-software-solutions` using
[Create GitHub App](https://github.com/organizations/adb-software-solutions/settings/apps/new).
The owner of the App and the accounts it can be installed on are separate choices.

This integration authenticates as the **App installation**, using the App's
signing key. People still sign into ADB through the existing Django-backed account
service. There is no GitHub user OAuth callback, GitHub login button or device flow
in this implementation. The GitHub username in **My work** is a filter preference.

The production values below use these two different destinations:

| Destination                     | Exact URL                                                                | What it does                                         |
| ------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------- |
| Dashboard / browser destination | `https://adbsoftwaresolutions.co.uk/admin/github`                        | Opens the protected dashboard in Software Solutions. |
| Webhook / server destination    | `https://api.adbsoftwaresolutions.co.uk/api/integrations/github/webhook` | Accepts signed POST deliveries in Django.            |

**Correction for the form in your screenshot:** delete the webhook address from
**Redirect URI** and leave that field blank. Put it in **Webhook URL** instead.
Also change the bottom selection from **Only on this account** to **Any account**.

## Fill in every registration field

Work down the form in this order. These recommendations match the implemented
backend, rather than adding an unused OAuth flow. GitHub describes the optional
registration controls in its [registration guide](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app).

### App identity

| Field           | Set it to                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| GitHub App name | `ADB Web Platform`. If GitHub says it is taken, choose another unique name; copy the resulting slug after creation. |
| Description     | Paste the description below.                                                                                        |
| Homepage URL    | `https://adbsoftwaresolutions.co.uk`                                                                                |

Suggested description:

```text
Internal ADB dashboard for repositories, issues, pull requests and GitHub Actions across our organisations. Includes workflow status, logs and controlled workflow dispatch and reruns.
```

### Identifying and authorizing users

| Field / checkbox                                       | Set it to                                                          |
| ------------------------------------------------------ | ------------------------------------------------------------------ |
| Redirect URI / Callback URL                            | **Blank.** Remove the existing entry with **Delete** if necessary. |
| Allow wildcard matching                                | **Unchecked.**                                                     |
| Expire user authorization tokens                       | **Leave checked.** The platform does not request user tokens.      |
| Request user authorization (OAuth) during installation | **Unchecked.**                                                     |
| Enable Device Flow                                     | **Unchecked.**                                                     |

A redirect URI is for receiving a user-authorization result. The webhook handler
accepts signed event POSTs and cannot process an OAuth redirect. No OAuth client
secret or user access token needs to be generated for the ADB integration.

### Post installation

| Field / checkbox   | Set it to                                         |
| ------------------ | ------------------------------------------------- |
| Setup URL          | `https://adbsoftwaresolutions.co.uk/admin/github` |
| Redirect on update | **Unchecked.**                                    |

The setup URL is a browser landing page after installation. Sign in if prompted,
then choose **Connections** and approve the installation as described below.
It does not automatically approve ownership or exchange an OAuth code. There is
no need to add an invented `/callback` route or a `?tab=connections` parameter.
See [GitHub's setup URL explanation](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/about-the-setup-url).

For a local browser preview, the Setup URL can instead be
`http://localhost:3000/admin/github`. This does **not** make a localhost webhook
reachable by GitHub; webhook delivery needs a public HTTPS backend address.

### Webhook

| Field / checkbox           | Set it to                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------- |
| Active                     | **Checked.**                                                                          |
| Webhook URL                | `https://api.adbsoftwaresolutions.co.uk/api/integrations/github/webhook`              |
| Secret                     | A newly generated random secret, also stored as `GITHUB_WEBHOOK_SECRET` in Infisical. |
| SSL verification, if shown | **Enabled.**                                                                          |

Use the exact webhook path above, with no extra trailing slash, query string,
`/admin` prefix or login page. It is registered directly in Django's URL config.
The public API host must route this endpoint to Django without an interactive
login challenge or proxy redirect.

To generate the secret, run this on your own machine and copy the output into
both GitHub's **Secret** field and Infisical's `GITHUB_WEBHOOK_SECRET` value:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The result is 64 hexadecimal characters. Store the value itself, with no added
quotes or spaces. This webhook secret and the RSA signing private key are
**different values** with different jobs: the secret verifies incoming deliveries;
the private key signs outgoing App authentication.

For local webhook testing, expose Django's port `8000` through your chosen HTTPS
tunnel. Use `https://YOUR-TUNNEL-HOST/api/integrations/github/webhook` in the
Webhook URL field. Tunnel Django, not the Next.js frontend. A separate development
App can keep local deliveries separate from the production App's endpoint.

### Permissions

Expand **Repository permissions** and set exactly these entries:

| Repository permission             | GitHub dropdown choice | Used by this code                                                         |
| --------------------------------- | ---------------------- | ------------------------------------------------------------------------- |
| Actions                           | **Read and write**     | Workflow/run/job views, logs, dispatch and failed-job reruns.             |
| Contents                          | **Read-only**          | Push subscriptions used to refresh workflow definitions.                  |
| Issues                            | **Read-only**          | Read issue details, authors and assignments.                              |
| Metadata                          | **Read-only**          | Repository and installation inventory; GitHub may set this automatically. |
| Pull requests                     | **Read-only**          | Read PR details, authors, assignments and requested reviewers.            |
| Every other repository permission | **No access**          | Not requested by the current implementation.                              |

In particular, leave **Workflows**, **Checks**, **Commit statuses**,
**Administration**, **Secrets** and **Dependabot alerts** at **No access**.
Viewing Dependabot PRs uses **Pull requests**, not Dependabot-alert access.
Dispatch uses the Actions REST API; the platform does not edit workflow YAML.
GitHub's [workflow-dispatch reference](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
requires Actions write access for that operation.

| Other permission group                     | Set every permission to |
| ------------------------------------------ | ----------------------- |
| Organization permissions                   | **No access**           |
| Account permissions                        | **No access**           |
| Enterprise permissions (preview), if shown | **No access**           |

Organisation installations are supported without granting organisation-wide
Members or Administration permissions. Actions write access gives the App the
remote capability to start/rerun work; ADB still checks each staff member's
separate workflow-trigger capability and repository scope.

### Subscribe to events

Select the permissions above **first**. GitHub then exposes the related event
checkboxes. The short initial list in your screenshot is not the complete list
available after permissions are selected.

Check only these six subscriptions:

| Checkbox label | Event name delivered to Django | Why it is used                                           |
| -------------- | ------------------------------ | -------------------------------------------------------- |
| Repository     | `repository`                   | Refresh repository inventory after changes.              |
| Issues         | `issues`                       | Refresh issue state and assignment.                      |
| Pull request   | `pull_request`                 | Refresh PR state and review requests, including bot PRs. |
| Push           | `push`                         | Refresh workflow definitions after repository changes.   |
| Workflow run   | `workflow_run`                 | Refresh pipeline/run status and results.                 |
| Workflow job   | `workflow_job`                 | Refresh run data as jobs change.                         |

Leave all other optional subscriptions unchecked, including **Installation
target**, **Meta** and **Security advisory** shown in the screenshot. These are
not the installation-created/repository-access events used by this integration.

`installation` and `installation_repositories` are delivered by default and
have no manual subscription checkbox. They create pending connections and update
repository access. See [GitHub's installation event reference](https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation)
and [repository-access event reference](https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories).

### Where can this GitHub App be installed?

Select **Any account**, then click **Create GitHub App**.

**Only on this account** would limit installation to `adb-software-solutions`
and prevent using this same App for the other organisations and your personal
account. Choosing Any account does not connect those accounts automatically;
you must install it on each one and approve the matching ADB connection.

## After creation: copy settings into Infisical

Open the App from
[adb-software-solutions App settings](https://github.com/organizations/adb-software-solutions/settings/apps)
and select its **General** page.

| Backend variable         | Where to get its value                                                         | Format                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `GITHUB_APP_ID`          | **App ID** on the App's settings page.                                         | Numeric ID, for example `123456`; use your actual number. This is not the Client ID.           |
| `GITHUB_APP_SLUG`        | Open the App's public page and copy the part after `https://github.com/apps/`. | For example `adb-web-platform` if that is the slug GitHub assigned. Do not paste the full URL. |
| `GITHUB_APP_PRIVATE_KEY` | **Private keys → Generate a private key**, then open the downloaded `.pem`.    | The complete unencrypted RSA PEM, including its BEGIN/END lines.                               |
| `GITHUB_WEBHOOK_SECRET`  | The random value you put in the registration form's **Secret** field.          | The identical secret text.                                                                     |

Store the PEM directly in Infisical and inject it into backend processes. Paste
it as a multiline secret; literal `\n` escapes also work. The key is not a file
path, a Vault credential ID or an OAuth client secret. Nothing needs bootstrapping
into application records. GitHub documents key generation on its
[private-key page](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps).

Set all four values for **Django, every Celery worker and Celery Beat**, then
restart/redeploy those processes. These are backend runtime settings, not
`NEXT_PUBLIC_*` variables or frontend build settings. On the App's General page,
leave **Client secrets** unused; the current platform does not use user OAuth.

In development the backend environment comes from `.devcontainer/.env` via
Compose's `env_file`; recreate the container after changing its values. Apply
migrations and run the existing workers and Beat before approving connections:

```bash
python backend/manage.py migrate
```

To rotate the signing key later, generate a replacement in GitHub, update
Infisical and redeploy Django/workers/Beat before deleting the old GitHub key.
Do not rotate the webhook secret at the same time unless you intend to change it
in both GitHub and Infisical too.

## Install the App and approve each connection

1. From the registered App's sidebar, click **Install App**.
2. Install that same App on each account in the settings-link table below:
   `adb-software-solutions`, `adb-web-designs`, `VastDesk`, `vanderheim-village`,
   `adambirds`, `adb-technology` and `switchonyourcode`.
3. Choose **All repositories** if existing and newly created repositories should
   join automatically. **Only select repositories** limits the dashboard to
   your chosen set and requires updating access when another repository is added.
4. Complete any required organisation-owner approval.
5. Open `https://adbsoftwaresolutions.co.uk/admin/github` (locally
   `http://localhost:3000/admin/github`) and click **Connections**. Signed
   installation events create pending entries after Celery processes them.
6. Choose **Choose ownership and approve**, select **Internal** for your own
   operational repositories or the relevant **Client**, then choose
   **Connect and synchronise**. Apply the ownership appropriate to that account;
   do not automatically assign every organisation to a Client.
7. If the installation happened before the webhook was working, enter its numeric
   installation ID manually in Connections. Find it by clicking **Configure** in
   the GitHub installation settings: a URL ending `/settings/installations/987654`
   means installation ID `987654`. That number is **not** the App ID.
8. Save `adambirds` as your GitHub username in the dashboard if you want **My work**
   to match your authored/assigned work and requested reviews. Dependabot PRs
   remain in their separate view.

Approval validates the installation against the configured App before importing
records. Registration alone does not install the App or create an approved
platform connection. The setup URL simply brings you back to the dashboard.

## Verify the setup and troubleshoot

Open your registered App's **Advanced → Recent Deliveries** page. Inspect a
`ping` or installation delivery and confirm it received a successful 2xx response.
The implemented handler returns **202** for a newly accepted delivery and **200**
for a duplicate. GitHub provides [delivery inspection](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/viewing-webhook-deliveries)
and [redelivery](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks) instructions.

Then confirm one approved connection synchronises repositories. Make a test
issue/PR change or run an existing workflow on a connected repository and check
that its dashboard data updates. An open GitHub dashboard refreshes through the
shared SSE stream after the worker finishes; successful webhook receipt alone
is not evidence that the worker completed processing.

| Symptom                                             | Check                                                                                                                                                                                    |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Only three event checkboxes are visible             | Set the repository permissions first; then choose the six subscriptions above.                                                                                                           |
| Other organisations cannot install the App          | Change installation availability to **Any account** and use the same App's Install App link.                                                                                             |
| Browser shows 405 at the webhook URL                | The browser made a GET. The endpoint accepts signed POST deliveries; use Recent Deliveries to test it.                                                                                   |
| GitHub delivery returns 403                         | GitHub's Secret and backend `GITHUB_WEBHOOK_SECRET` must match exactly. Check signature-header/body forwarding.                                                                          |
| GitHub delivery returns 503                         | The receiving Django process has no webhook secret configured. Redeploy with the secret.                                                                                                 |
| GitHub delivery returns 404 or redirects            | Check the backend hostname, exact path, HTTPS routing and proxy/login rules.                                                                                                             |
| Delivery succeeds but no pending connection appears | Check Celery workers/Beat and redeliver the installation event, or enter its installation ID manually. A ping alone creates no connection.                                               |
| Connection exists but no repositories appear        | Approve its ownership, check All/selected repository access, run Synchronise now and inspect its displayed sync error.                                                                   |
| GitHub API returns 401                              | Check App ID, PEM formatting/key validity and server time; redeploy all backend processes after key changes.                                                                             |
| GitHub API returns 403                              | Check App installation access and accepted permission updates. GitHub API 403s can also be caused by rate limits or organisation policy; inspect the integration error/delivery context. |
| Workflow cannot be started                          | Grant Actions read/write, use a workflow with `workflow_dispatch`, choose a valid ref and grant the ADB trigger capability.                                                              |
| App permissions were changed after installation     | Approve the permission update on every affected installation; saving the App registration alone does not grant new access to existing installations.                                     |

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
