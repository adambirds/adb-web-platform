# Authentication and account security

Django is the single identity/session authority. The browser counterpart is the
[dedicated account application](../../sites/auth-adb-software-solutions/README.md).

| Location                                                    | Responsibility                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------ |
| [models.py](./models.py)                                    | User and shared identity models                              |
| [backends.py](./backends.py)                                | Authentication backends                                      |
| [auth_service/](./auth_service/)                            | Login, account and recovery endpoints; `tests/` covers views |
| [twofactor/](./twofactor/)                                  | TOTP, recovery codes, models and `tests/`                    |
| [passkeys/](./passkeys/)                                    | WebAuthn verification, models, security logs and `tests/`    |
| [sessions/](./sessions/)                                    | Session models, helpers and management endpoints             |
| [ninja/](./ninja/)                                          | Shared identity API contracts                                |
| [queries.py](./queries.py) / [mutations.py](./mutations.py) | Identity reads and writes                                    |
| [ratelimit.py](./ratelimit.py)                              | Authentication throttling                                    |
| [migrations/](./migrations/)                                | Identity database history                                    |
| [templates/](./templates/)                                  | Server-owned authentication templates                        |

Run `tools/test-backend authentication` from the repository root, or select a
subdomain such as `authentication.passkeys.tests`. Business staff capabilities
and Client/Queue scopes belong in [access_control](../apps/access_control/README.md).
See the [backend guide](../README.md) and
[permissions model](../../docs/PERMISSIONS_AND_ACCESS_MODEL.md) before changing
security behaviour.
