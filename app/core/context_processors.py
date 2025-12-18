def context_vars(request):
    from django.conf import settings

    if "admin" in request.META["PATH_INFO"]:
        return {}

    context = {}
    context["DATE"] = settings.DATE_FORMAT
    context["DATETIME"] = settings.DATETIME_FORMAT
    context["DATETIME_ALAS"] = settings.DATETIME_FORMAT_ALAS
    context["TESTING"] = settings.TESTING if hasattr(settings, "TESTING") else False

    return context
