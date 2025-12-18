from django.contrib import admin
from django.utils.html import format_html

from persona.models import Academico
from universidad.models import SecretarioInstitucion, SecretarioInstitucionInvitacion, Unidad, Universidad


class PaisFilter(admin.SimpleListFilter):
    title = "país"
    parameter_name = "pais"

    def lookups(self, _, model_admin):
        pais = {c.universidad.pais for c in model_admin.model.objects.all()}
        return [(p, p) for p in pais]

    def queryset(self, _, queryset):
        if self.value():
            return queryset.filter(universidad__pais=self.value())
        return None


class UniversidadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "sigla",
        "pais",
        "casa_central",
        "pagina",
        "is_cruch",
        "id_externo",
        "is_manual",
    )
    list_filter = ("pais",)
    search_fields = ["nombre", "sigla", "pais"]

    def pagina(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.webpage)

    def is_cruch(self, obj):
        return obj.is_cruch

    def id_externo(self, obj):
        return bool(obj.id_ringgold) or bool(obj.id_wikidata) or bool(obj.id_ror) or bool(obj.id_isni) or bool(obj.id_crossref)

    is_cruch.boolean = True
    id_externo.short_description = "CRUCH"
    id_externo.boolean = True
    id_externo.short_description = "Tiene id externo"


class UnidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sigla", "universidad", "pagina", "is_manual", "academicos")
    list_filter = (
        PaisFilter,
        "universidad",
    )
    search_fields = [
        "nombre",
        "sigla",
        "universidad__nombre",
    ]

    def pagina(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.webpage)

    def academicos(self, obj):
        return Academico.objects.filter(unidad=obj).count()


class SecretarioInstitucionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "institucion",
    )
    list_filter = ("institucion",)


class SecretarioInstitucionInvitacionAdmin(admin.ModelAdmin):
    list_display = (
        "institucion",
        "code",
        "expiration",
        "is_confirmed",
    )
    list_filter = ("institucion",)


admin.site.register(Universidad, UniversidadAdmin)
admin.site.register(Unidad, UnidadAdmin)
admin.site.register(SecretarioInstitucion, SecretarioInstitucionAdmin)
admin.site.register(SecretarioInstitucionInvitacion, SecretarioInstitucionInvitacionAdmin)
