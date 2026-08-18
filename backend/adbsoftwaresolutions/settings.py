"""Django settings for the shared ADB Business Platform backend."""

import base64
import binascii
import logging
import os
from pathlib import Path

import django_stubs_ext
from django.templatetags.static import static

logger = logging.getLogger(__name__)

DEBUG = bool(int(os.environ.get("DEBUG", "0")))
DEBUG_TOOLBAR_ENABLED = bool(int(os.environ.get("DEBUG_TOOLBAR_ENABLED", "0")))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set.")

if DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "localhost")
ADMIN_FRONTEND_URL = os.environ.get("ADMIN_FRONTEND_URL", "http://localhost:3000")
AUTH_FRONTEND_URL = os.environ.get("AUTH_FRONTEND_URL", "http://localhost:3004")
SOFTWARE_SOLUTIONS_FRONTEND_URL = os.environ.get(
    "SOFTWARE_SOLUTIONS_FRONTEND_URL",
    "http://localhost:3001",
)
WEB_DESIGNS_FRONTEND_URL = os.environ.get(
    "WEB_DESIGNS_FRONTEND_URL",
    "http://localhost:3002",
)
TECHNOLOGY_FRONTEND_URL = os.environ.get(
    "TECHNOLOGY_FRONTEND_URL",
    "http://localhost:3003",
)

# Kept as a compatibility alias while older email/auth code is migrated to the
# explicit application URLs above.
FRONTEND_URL = os.environ.get("FRONTEND_URL", SOFTWARE_SOLUTIONS_FRONTEND_URL)

if not SITE_DOMAIN:
    raise ValueError("SITE_DOMAIN must be set.")

if DEBUG:
    ALLOWED_HOSTS: list[str] = ["*"]
else:
    ALLOWED_HOSTS = [
        "api." + SITE_DOMAIN,
    ]

INSTALLED_APPS = [
    "authentication",
    "apps.core",
    "apps.access_control",
    "apps.website",
    "apps.clients",
    "apps.infrastructure",
    "apps.crm",
    "apps.credentials",
    "apps.knowledge_base",
    "apps.tasks",
    "apps.ticketing",
    "corsheaders",
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

UNFOLD = {
    "SITE_TITLE": "ADB Business Platform",
    "SITE_HEADER": "ADB Business Platform",
    "SITE_ICON": {
        "light": lambda request: static("logo.png"),
        "dark": lambda request: static("logo-dark.png"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("logo.png"),
        "dark": lambda request: static("logo-dark.png"),
    },
}

if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ["debug_toolbar"]

AUTH_USER_MODEL = "authentication.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ninja.compatibility.files.fix_request_files_middleware",
]

if DEBUG_TOOLBAR_ENABLED:
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

AUTHENTICATION_BACKENDS = [
    "authentication.backends.EmailBackend",
]

ROOT_URLCONF = "adbsoftwaresolutions.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]

ASGI_APPLICATION = "adbsoftwaresolutions.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("SQL_DATABASE", "app_dev"),
        "USER": os.environ.get("SQL_USER", "app"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "app_dev_password"),
        "HOST": os.environ.get("SQL_HOST", "db"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
        "OPTIONS": {
            "sslmode": os.environ.get("SQL_SSL", "disable"),
        },
    }
}


def decode_base64(value: str) -> str:
    """Decode base64-encoded configuration values while accepting plain text."""
    try:
        decoded_value = base64.b64decode(value).decode("utf-8")
        return decoded_value
    except (binascii.Error, UnicodeDecodeError):
        return value


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

django_stubs_ext.monkeypatch()

SITE_ID = 1
SITE_NAME = "ADB Business Platform"

X_FRAME_OPTIONS = "SAMEORIGIN"

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = "." + SITE_DOMAIN if not DEBUG else None

CORS_ALLOWED_ORIGINS = [
    "https://" + SITE_DOMAIN,
    "https://api." + SITE_DOMAIN,
    "https://auth." + SITE_DOMAIN,
    "https://admin." + SITE_DOMAIN,
    "https://adbwebdesigns.co.uk",
    "https://www.adbwebdesigns.co.uk",
    "https://adbtechnology.co.uk",
    "https://www.adbtechnology.co.uk",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
    ]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "X-CSRFToken",
    "sentry-trace",
    "baggage",
]

CORS_ALLOW_CREDENTIALS = True

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 864000
SESSION_COOKIE_DOMAIN = "." + SITE_DOMAIN if not DEBUG else None

SESSION_CACHE_ALIAS = "session"

DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("CACHE_BACKEND_URL", ""),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "session": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("SESSION_BACKEND_URL", ""),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

if DEBUG:
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    RATE_LIMIT_DISABLED = True
