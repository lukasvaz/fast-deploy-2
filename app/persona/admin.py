from django.contrib import admin
from django.utils.html import format_html

from persona.models import (
    Academico,
    AcademicoInvitacion,
    AmbitoTrabajo,
    Area,
    CoautorInvestigador,
    Dominio,
    DominioAcademico,
    InvestigadorCandidato,
    InvestigadorOnDemand,
    Keyword,
    KeywordInvestigador,
    Subarea,
)


class InvestigadorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "apellido",
        "orcid_rol",
        "orcid_link",
    )
    list_filter = ("activo",)
    search_fields = ["nombre", "apellido", "dblp_id"]

    def orcid_link(self, obj):
        return format_html(
            "<a href='{url}'>{orcid}</a>",
            url="https://orcid.org/" + obj.orcid_id,
            orcid=obj.orcid_id,
        )


class InvestigadorOnDemandAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre_completo",
        "dblp_link",
    )
    list_filter = ("activo",)
    search_fields = ["nombre", "apellido", "dblp_id"]

    def nombre_completo(self, obj):
        if obj.apellido:
            return obj.nombre + " " + obj.apellido
        else:
            return obj.nombre

    def dblp_link(self, obj):
        return format_html(
            "<a href='{url}'>{dblp_id}</a>",
            url=f"https://dblp.org/pid/{obj.dblp_id}.html",
            dblp_id=obj.dblp_id,
        )


class InvestigadorCandidatoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buscado",
        "valid",
        "results",
        "valid_result",
    )

    def results(self, obj):
        return len(obj.candidatos)

    def valid_result(self, obj):
        if len(obj.candidatos) == 1:
            first = obj.candidatos[0]
            return format_html(
                "<a href='{url}'>{dblp_id}</a>",
                url=f"https://dblp.org/pid/{first}.html",
                dblp_id=first,
            )
        else:
            return


class AcademicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "apellido",
        "unidad",
        "universidad",
    )
    # list_filter = (,)
    search_fields = ["nombre", "apellido"]

    def universidad(self, obj):
        if not obj.unidad:
            return None
        return obj.unidad.universidad.sigla

    # def dblp_link(self, obj):
    #     return format_html(
    #         "<a href='{url}'>{dblp}</a>",
    #         url="https://dblp.org/pid/" + obj.dblp_id,
    #         dblp=obj.dblp_id,
    #     )

    # def orcid_link(self, obj):
    #     if obj.orcid_id:
    #         return format_html(
    #             "<a href='{url}'>{orcid}</a>",
    #             url="https://orcid.org/" + obj.orcid_id,
    #             orcid=obj.orcid_id,
    #         )
    #     else:
    #         inv = InvestigadorOnDemand.objects.get(dblp_id=obj.dblp_id)
    #         if inv.orcid_id:
    #             return format_html(
    #                 "<a href='{url}'>{orcid}</a>",
    #                 url="https://orcid.org/" + inv.orcid_id,
    #                 orcid=inv.orcid_id,
    #             )


class DominioAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ["nombre"]


class DominioAcademicoAdmin(admin.ModelAdmin):
    # list_display = ('image', 'paragraph','created',)
    pass


class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre_es", "nombre_en")
    search_fields = ["nombre_es", "nombre_en"]


class SubareaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_es",
        "nombre_en",
        "area",
    )
    list_filter = ("area",)
    search_fields = ["nombre", "area__nombre"]


class KeywordAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        # "specificarea",
    )
    # list_filter = ("area",)
    search_fields = ["nombre"]


class AmbitoTrabajoAdmin(admin.ModelAdmin):
    search_fields = ["academico__nombre"]


class KeywordInvestigadorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_investigador",
        "keyword",
        "peso",
    )

    search_fields = ["investigador__nombre"]

    def nombre_investigador(self, obj):
        return obj.investigador.nombre


class CoautorInvestigadorAdmin(admin.ModelAdmin):
    list_display = (
        "investigador_a",
        "investigador_b",
        "peso",
    )


class AcademicoInvitacionAdmin(admin.ModelAdmin):
    list_display = (
        "academico",
        "code",
        "expiration",
        "is_confirmed",
    )


admin.site.register(InvestigadorOnDemand, InvestigadorOnDemandAdmin)
admin.site.register(InvestigadorCandidato, InvestigadorCandidatoAdmin)
admin.site.register(Academico, AcademicoAdmin)
admin.site.register(Dominio, DominioAdmin)
admin.site.register(DominioAcademico, DominioAcademicoAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Subarea, SubareaAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(AmbitoTrabajo, AmbitoTrabajoAdmin)
admin.site.register(KeywordInvestigador, KeywordInvestigadorAdmin)
admin.site.register(CoautorInvestigador, CoautorInvestigadorAdmin)
admin.site.register(AcademicoInvitacion, AcademicoInvitacionAdmin)
