import logging
import os
from datetime import datetime as dt

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import get_current_timezone

logger = logging.getLogger(__name__)


def get_env_variable(var_name, default=None):
    try:
        var = os.environ[var_name]
        if var.lower() == "true":
            return True
        elif var.lower() == "false":
            return False
        return var
    except KeyError:
        if default:
            return default
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)


def str_to_date(str):
    return dt.strptime(str[:10], "%Y-%m-%d").replace(tzinfo=get_current_timezone())


def str_to_datetime(str):
    return dt.strptime(str[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=get_current_timezone())


def format_date(date):
    return date.strftime("%d/%m/%Y")


def format_datetime(date, alas=False):
    return date.strftime("%d/%m/%Y a las %H:%M:%S" if alas else "%d/%m/%Y %H:%M:%S")


def get_current_datetime():
    return dt.now().replace(tzinfo=get_current_timezone())


def handle_exception(msg: str = ""):
    from rich.console import Console

    console = Console()
    console.print_exception(show_locals=True)
    logger.error(console.print_exception(show_locals=True))


def log_and_print(msgs):
    from rich.pretty import pprint

    logger.info(msgs)
    pprint(msgs)


def mover_archivo(origen: str, destino: str):
    try:
        os.makedirs(settings.MEDIA_ROOT + f"/{os.path.dirname(destino)}", exist_ok=True)
        os.rename(settings.MEDIA_ROOT + f"/{origen}", settings.MEDIA_ROOT + f"/{destino}")
    except Exception:
        handle_exception()
        return origen
    else:
        return destino
