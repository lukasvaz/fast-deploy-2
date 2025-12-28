from core.settings.base import *
from pathlib import Path

MEDIA_URL = "/media/"
MEDIA_ROOT = Path("/data/media")

DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "apps.dcc.uchile.cl",
    "test.dcc.uchile.cl",
    "labs.test.dcc.uchile.cl",
    "fast-deploy-2.onrender.com",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "https://apps.dcc.uchile.cl",
    "https://test.dcc.uchile.cl",
    "https://labs.test.dcc.uchile.cl",
    "https://fast-deploy-2.onrender.com",
]


USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]
