from django.conf import settings

from core.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

STATIC_ROOT = settings.BASE_DIR / "data/static"
MEDIA_ROOT = settings.BASE_DIR / "data/media"
