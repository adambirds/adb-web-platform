# Django project configuration

This package assembles the shared backend rather than owning a business domain.

| Location                                                  | Responsibility                                                   |
| --------------------------------------------------------- | ---------------------------------------------------------------- |
| [settings.py](./settings.py)                              | Environment, installed apps, databases and service configuration |
| [settings_test.py](./settings_test.py)                    | Test settings overrides                                          |
| [urls.py](./urls.py)                                      | Root URL registration                                            |
| [ninja/routers.py](./ninja/routers.py)                    | Shared API assembly                                              |
| [celery.py](./celery.py) / [bootsteps.py](./bootsteps.py) | Worker bootstrap and task discovery                              |
| [asgi.py](./asgi.py) / [wsgi.py](./wsgi.py)               | Server entrypoints                                               |
| [asgi_middleware.py](./asgi_middleware.py)                | ASGI middleware                                                  |
| [tests/](./tests/)                                        | Celery discovery and Redis configuration regressions             |

Run `tools/test-backend adbsoftwaresolutions.tests` from the repository root.
See the [backend guide](../README.md) for domain navigation and conventions.
