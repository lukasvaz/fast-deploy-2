import json

from django.conf import settings
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect


def infoView(request, *args, **kwargs):
    with open(settings.BASE_DIR / "info.json", "r") as json_file:
        return JsonResponse(json.load(json_file))


class CustomReleaseUserView(ReleaseUserView):
    """
    Se ejecuta cuando un usuario usurpado, es liberado.
    """

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return HttpResponseRedirect(settings.BASE_URL)
