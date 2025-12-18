from braces.views import MessageMixin
from django.views.generic import View


class CoreMessageMixin(MessageMixin):
    def msg_success(self, msg, desc=None):
        self.messages.success(f"<span class='fw-bold'>{desc}:</span> {msg}" if desc else f"{msg}")

    def msg_info(self, msg, desc=None):
        self.messages.info(f"<span class='fw-bold'>{desc}:</span> {msg}" if desc else f"{msg}")

    def msg_warning(self, msg, desc=None):
        self.messages.warning(f"<span class='fw-bold'>{desc}:</span> {msg}" if desc else f"{msg}")

    def msg_error(self, msg, desc=None):
        self.messages.error(f"<span class='fw-bold'>{desc}:</span> {msg}" if desc else f"{msg}")

    def msg_guardado(self, msg=None):
        return self.msg_success(msg, desc="Guardado") if msg else self.msg_success("Guardado")

    def msg_eliminado(self, msg=None):
        return self.msg_success(msg, desc="Eliminado") if msg else self.msg_succes("Eliminado")

    def msg_requeridos(self):
        return self.msg_warning("Completa todos los datos requeridos")


class CoreModuleViewMixin(CoreMessageMixin, View):
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["icons"] = {
            # common
            "faq": "bi bi-question-octagon-fill",
            "historial": "bi bi-clock-history",
            # varios
            "pdf": "bi bi-file-pdf-fill",
            "listar": "bi bi-list-ul",
            # navegacion
            "volver": "bi bi-arrow-left-square-fill",
            # forms
            "agregar": "bi bi-plus-square-fill",
            "editar": "bi bi-pencil-fill",
            "guardar": "bi bi-floppy-fill",
            "cancelar": "bi bi-x-square-fill",
            "eliminar": "bi bi-trash-fill",
            "upload": "bi bi-cloud-upload-fill",
            # alertas
            "warning": "bi-exclamation-circle-fill",
            "success": "bi-check-circle-fill",
            "info": "bi-info-circle-fill",
            "danger": "bi-x-circle-fill",
        }
        return context
