from core.settings.base import *

DEBUG = False

ALLOWED_HOSTS = [
    "apps.dcc.uchile.cl",
    "test.dcc.uchile.cl",
    "labs.test.dcc.uchile.cl",
    "fast-deploy-2.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://apps.dcc.uchile.cl",
    "https://test.dcc.uchile.cl",
    "https://labs.test.dcc.uchile.cl",
    "https://fast-deploy-2.onrender.com",
]

ADMINS = [
    # ("Área de Desarrollo de Software", "desarrollo@dcc.uchile.cl"),
]


# test https in request.scheme, read X-Forwarded-Proto from nginx
# If its value is "https"
# Then set:
# request.scheme → "https"
# request.is_secure() → True

##*****IMPORTANT***** TODO:ADD THIS HEADER IN NGINX CONFIG X-Forwarded-Proto:https:

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
       "whitenoise.middleware.WhiteNoiseMiddleware",
]

STATIC_FILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

INSTALLED_APPS += ["sendfile"]

MEDIA_ROOT = "/data/media"
MEDIA_URL = "/media/"
SENDFILE_BACKEND = "sendfile.backends.simple"
