from rest_framework import serializers

from grados.models import GradoInstancia, GradoTipo
from persona.models import Academico, AmbitoTrabajo, Area, Subarea
from universidad.models import Unidad, Universidad


# Serializers for the API
class ApiUnidadSerializer(serializers.ModelSerializer):
    """Serializer for Unidad model."""

    class Meta:
        model = Unidad
        fields = ["nombre", "sigla", "webpage"]


class ApiGradoSerializer(serializers.ModelSerializer):
    """Serializer for Grado model."""

    afiliacion = serializers.SerializerMethodField()

    class Meta:
        model = GradoInstancia
        fields = ["id", "nombre", "tipo", "afiliacion", "web_site", "fecha_creacion"]

    def get_afiliacion(self, obj):
        unidad_data = ApiUnidadSerializer(obj.unidad).data
        universidad_data = ApiInstitutionDehydratedSerializer(obj.unidad.universidad).data
        return {"unidad": unidad_data, "universidad": universidad_data}


class ApiInstitutionSerializer(serializers.ModelSerializer):
    """Serializer for Institution model."""

    external_ids = serializers.SerializerMethodField()
    web_page = serializers.SerializerMethodField()
    acronimos = serializers.SerializerMethodField()
    geo_data = serializers.SerializerMethodField()

    class Meta:
        model = Universidad
        fields = ["id", "nombre", "pais", "acronimos", "web_page", "external_ids", "geo_data"]

    def get_acronimos(self, obj):
        return obj.get_alternative_siglas

    def get_web_page(self, obj):
        return obj.get_webpage

    def get_external_ids(self, obj):
        openalex_inst = getattr(obj, "openalex_institution", None)
        if not openalex_inst:
            return {}
        return {
            "openalex_id": getattr(openalex_inst, "openalex_id", None),
            "mag_id": getattr(openalex_inst, "openalex_id_mag", None),
            "grid_id": getattr(openalex_inst, "openalex_id_grid", None),
            "ror_id": getattr(openalex_inst, "openalex_id_ror", None),
            "wikidata_id": getattr(openalex_inst, "openalex_id_wikidata", None),
            "wikipedia_id": getattr(openalex_inst, "openalex_id_wikipedia", None),
        }

    def get_geo_data(self, obj):
        openalex_inst = getattr(obj, "openalex_institution", None)
        if not openalex_inst:
            return {}
        return {
            "latitude": openalex_inst.openalex_region_latitude,
            "longitude": openalex_inst.openalex_region_longitude,
            "city": openalex_inst.openalex_city_name,
            "city_id": openalex_inst.openalex_city_id,
        }


class ApiInstitutionDehydratedSerializer(ApiInstitutionSerializer):
    class Meta(ApiInstitutionSerializer.Meta):
        fields = ["id", "nombre", "pais", "acronimos", "web_page"]


class ApiAcademicoSerializer(serializers.ModelSerializer):
    """Serializer for Acaemico model. Includes related grado and institution (depth=1)."""

    afiliacion = serializers.SerializerMethodField()
    external_ids = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()

    class Meta:
        model = Academico
        fields = ["id", "nombre", "apellido", "webpage", "grado_maximo", "afiliacion", "external_ids", "areas"]

    def get_afiliacion(self, obj):
        unidad_data = ApiUnidadSerializer(obj.unidad).data
        universidad_data = ApiInstitutionDehydratedSerializer(obj.unidad.universidad).data
        return {"unidad": unidad_data, "universidad": universidad_data}

    def get_webpage(self, obj):
        return obj.get_webpage

    def get_external_ids(self, obj):
        if not getattr(obj, "investigador_ondemand", None):
            return {}
        else:
            io = obj.investigador_ondemand
            return {
                "dblp_id": io.dblp_id,
                "aminer_id": io.aminer_id,
                "openalex_id": io.openalex_id,
                "orcid_id": io.orcid_id,
            }

    def get_areas(self, obj):
        res = {"areas": [], "keywords": []}
        ambitos_query_otros = AmbitoTrabajo.objects.filter(academico=obj).order_by("-peso")
        for ambito_obj in ambitos_query_otros:
            res["areas"].append({"id": ambito_obj.subarea.area.id, "nombre": ambito_obj.subarea.area.nombre, "subareas": []})
            ambitos_query = (
                AmbitoTrabajo.objects.filter(academico=obj).filter(subarea__area__id=ambito_obj.subarea.area.id).order_by("-peso")
            )
            for ambito_2_obj in ambitos_query:
                res["areas"][-1]["subareas"].append({"nombre": ambito_2_obj.subarea.nombre, "peso": ambito_2_obj.peso})
        if getattr(obj, "investigador_ondemand", None) and getattr(obj.investigador_ondemand, "aminer_id", None):
            key_inv_query = obj.investigador_ondemand.aminer_profile.aminer_interests
            for nombre, peso in key_inv_query.items():
                res["keywords"].append({"nombre": nombre, "peso": peso})
        return res


class ApiAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "nombre"]


class ApiSubareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subarea
        fields = ["id", "nombre"]


# query serializers -> for query params validation
class AcademicoQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True, max_length=50)


# additional query serializers for strict query-param validation
class AcademicoAdvancedQuerySerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, allow_blank=True, max_length=100)
    institucion = serializers.CharField(required=False, allow_blank=True, max_length=200)
    pais_code = serializers.CharField(required=False, allow_blank=True, max_length=100)
    area = serializers.CharField(required=False, allow_blank=True, max_length=100)
    subarea = serializers.CharField(required=False, allow_blank=True, max_length=100)
    # keyword = serializers.CharField(required=False, allow_blank=True, max_length=100)
    page = serializers.IntegerField(required=False, min_value=1)


class InstitucionQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True, max_length=200)
    page = serializers.IntegerField(required=False, min_value=1)


class GradoSearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True, max_length=200)
    page = serializers.IntegerField(required=False, min_value=1)


class GradoAdvancedQuerySerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, allow_blank=True, max_length=200)
    universidad = serializers.CharField(required=False, allow_blank=True, max_length=200)
    tipo = serializers.CharField(required=False, allow_blank=True, max_length=50)
    page = serializers.IntegerField(required=False, min_value=1)

    def validate_tipo(self, value):
        valid_types = [choice[0] for choice in GradoTipo.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid tipo. Valid options are: {', '.join(valid_types)}")
        return value


class SubareasByAreaQuerySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, min_value=1)


class AcademicoGetIdQuerySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, min_value=1)
    dblp = serializers.CharField(required=False, allow_blank=True, max_length=200)
    orcid = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate(self, data):
        if not (data.get("id") or data.get("dblp") or data.get("orcid")):
            raise serializers.ValidationError("At least one of 'id', 'dblp' or 'orcid' must be provided")
        return data


class InstitucionGetIdQuerySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, min_value=1)
    openalex_id = serializers.CharField(required=False, allow_blank=True, max_length=200)
    ror_id = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate(self, data):
        if not (data.get("id") or data.get("openalex_id") or data.get("ror_id")):
            raise serializers.ValidationError("At least one of 'id', 'openalex_id' or 'ror_id' must be provided")
        return data
