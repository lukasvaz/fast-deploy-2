from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Simple health check endpoint for Docker healthcheck"""
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path("health", health_check, name="health"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
