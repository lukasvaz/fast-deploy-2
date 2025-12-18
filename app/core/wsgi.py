import os

from django.core.wsgi import get_wsgi_application

_application = get_wsgi_application()


def application(environ, start_response):
    # Only patch PATH_INFO in production (Gunicorn)
    if os.environ.get("SCRIPT_NAME") == "/docencia/acad_micros/":
        path_info = environ.get("PATH_INFO", "")
        if not path_info.startswith("/") and path_info:
            path_info = "/" + path_info
            environ["PATH_INFO"] = path_info
    print(
        f"DEBUG: WSGI Request. PATH_INFO={environ.get('PATH_INFO')}, SCRIPT_NAME={environ.get('SCRIPT_NAME')}, HTTP_HOST={environ.get('HTTP_HOST')}"
    )
    return _application(environ, start_response)
