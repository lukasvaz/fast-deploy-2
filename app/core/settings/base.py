import os
from pathlib import Path

from celery.schedules import crontab

from core.functions import get_env_variable

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY", "django-insecure-reemplazame!")

# Django
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django_countries",
    "django_jsonform",
    "django_cron",
    "rest_framework",
]


# 3rd party
INSTALLED_APPS += [
    "django_extensions",
    "modeltranslation",
]

# APPS
INSTALLED_APPS += [
    "persona",
    "universidad",
    "users",
    "etl",
    "grados",
    "front",
    "api",
    "revision",
]

CRON_CLASSES = [
    # "etl.cron.CargaAutomaticaCronJob",
    "etl.cron.DblpFetchCronJob",
    "etl.cron.AminerFetchCronJob",
    "etl.cron.OpenAlexFetchCronJob",
    "etl.cron.DblpUpdateCronJob",
    "etl.cron.AminerUpdateCronJob",
    "etl.cron.OpenAlexUpdateCronJob",
    "etl.cron.ValidateGradoUrlCronJob",
    "etl.cron.DeleteUnusedInvestigadorOnDemandCronJob",
]

LOGIN_REDIRECT_URL = "front:index"
LOGOUT_REDIRECT_URL = "front:index"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "_templates",
            "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.context_vars",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": get_env_variable("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": get_env_variable("DJANGO_DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": get_env_variable("DJANGO_DB_USER", ""),
        "PASSWORD": get_env_variable("DJANGO_DB_PASSWORD", ""),
        "HOST": get_env_variable("DJANGO_DB_HOST", ""),
        "PORT": get_env_variable("DJANGO_DB_PORT", ""),
    }
}

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

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_L10N = False
USE_TZ = True

# pylint: disable=C3001
gettext = lambda s: s
LANGUAGES = (
    ("es", gettext("Spanish")),
    ("en", gettext("English")),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_PREPOPULATE_LANGUAGE = "en"

DATETIME_FORMAT = "d/m/Y H:i"
DATETIME_FORMAT_ALAS = "d/m/Y \\a \\l\\a\\s H:i"
DATE_FORMAT = "d/m/Y"

STATIC_URL = "static/"
STATIC_ROOT = get_env_variable("DJANGO_STATIC_ROOT", "/static")
STATICFILES_DIRS = ["_staticfiles"]

MEDIA_ROOT = get_env_variable("DJANGO_MEDIA_ROOT", "/media")
MEDIA_URL = get_env_variable("DJANGO_MEDIA_URL", "media/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

EMAIL_BACKEND = get_env_variable("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = get_env_variable("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = get_env_variable("DJANGO_EMAIL_PORT", 587)
EMAIL_USE_TLS = get_env_variable("DJANGO_EMAIL_USE_TLS", True)
EMAIL_HOST_USER = get_env_variable("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("DJANGO_EMAIL_HOST_PASSWORD", "")

SERVER_EMAIL = get_env_variable("DJANGO_SERVER_EMAIL", "no-reply@dcc.uchile.cl")

LOGIN_URL = "/admin/login/"

# rest framework settings
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

SESSION_COOKIE_PATH = get_env_variable("DJANGO_COOKIE_PATH", "/")
CSRF_COOKIE_PATH = get_env_variable("DJANGO_COOKIE_PATH", "/")
LANGUAGE_COOKIE_PATH = get_env_variable("DJANGO_COOKIE_PATH", "/")

ADMINS = [
    ("Área de Desarrollo de Software", "desarrollo@dcc.uchile.cl"),
]

BASE_URL = get_env_variable("DJANGO_BASE_URL")

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "mail_admins": {
#             "level": "ERROR",
#             "class": "django.utils.log.AdminEmailHandler",
#             "include_html": True,
#         },
#         "logfile": {
#             "level": "INFO",
#             "class": "logging.handlers.RotatingFileHandler",
#             "filename": "/logs/ops-proxydos.log",
#             "maxBytes": 1 * 1024 * 1024,
#             "backupCount": 4,
#         },
#     },
#     "loggers": {
#         "django.request": {
#             "handlers": ["mail_admins"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#         "django": {
#             "handlers": ["logfile"],
#             "level": "INFO",
#             "propagate": True,
#         },
#     },
# }

# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": [
#         "rest_framework.authentication.TokenAuthentication",
#         "rest_framework.authentication.BasicAuthentication",
#         "rest_framework.authentication.SessionAuthentication",
#     ],
#     "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"],
#     "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
#     "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
#     "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
#     "PAGE_SIZE": 100,  # Define cuántos elementos quieres mostrar por página
# }

# SPECTACULAR_SETTINGS = {
#     "TITLE": "DCC APIs",
#     "DESCRIPTION": "DCC proxydos APIs",
#     "VERSION": "1.0.0",
#     "SERVE_INCLUDE_SCHEMA": False,
#     "SWAGGER_UI_DIST": "SIDECAR",
#     "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
#     "REDOC_DIST": "SIDECAR",
#     "CONTACT": {
#         "name": "ati@dcc.uchile.cl",
#         "url": "dcc.uchile.cl",
#         "email": "ati@dcc.uchile.cl",
#     },
#     "SERVERS": [{"url": get_env_variable("DJANGO_SPECTACULAR_SERVER")}],
# }

# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"https:\/\/(.)*(dcc|ing).uchile.cl",
#     r"http:\/\/localhost(.)*",
# ]
