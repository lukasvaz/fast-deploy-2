from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value
from django.db.models.functions import Coalesce, Concat, Greatest
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.serializers import (
    AcademicoAdvancedQuerySerializer,
    AcademicoGetIdQuerySerializer,
    AcademicoQuerySerializer,
    ApiAcademicoSerializer,
    ApiAreaSerializer,
    ApiGradoSerializer,
    ApiInstitutionSerializer,
    ApiSubareaSerializer,
    GradoAdvancedQuerySerializer,
    GradoSearchQuerySerializer,
    InstitucionGetIdQuerySerializer,
    InstitucionQuerySerializer,
    SubareasByAreaQuerySerializer,
)
from grados.models import GradoInstancia
from persona.models import (
    Academico,
    AmbitoTrabajo,
    Area,
    DblpProfile,
    InvestigadorOnDemand,
    OpenAlexProfile,
    Subarea,
)
from universidad.models import OpenAlexInsitution, Universidad


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


class AcademicoSearchBasicView(ListAPIView):
    serializer_class = ApiAcademicoSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Academico.objects.all()

    def get_queryset(self):
        # reject unknown params
        incoming = set(self.request.query_params.keys())
        allowed = set(AcademicoQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        # params validation
        qser = AcademicoQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)

        params = qser.validated_data
        # filtering
        qs = (
            Academico.objects.annotate(
                similarity=TrigramSimilarity(
                    Concat(
                        Coalesce("nombre", Value("")),
                        Value(" "),
                        Coalesce("apellido", Value("")),
                    ),
                    params.get("query"),
                )
            )
            .filter(similarity__gt=0.15)
            .order_by("-similarity")
        )
        return qs

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademicoSearchAdvancedView(ListAPIView):
    serializer_class = ApiAcademicoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(AcademicoAdvancedQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = AcademicoAdvancedQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        query_nombre = params.get("nombre")
        query_institucion = params.get("institucion", "")
        query_pais_code = params.get("pais_code", "")
        query_area = params.get("area", "")
        query_subarea = params.get("subarea", "")
        # query_keyword = params.get("keyword", "")
        qs = Academico.objects.all()
        if query_nombre:
            qs = (
                Academico.objects.annotate(
                    similarity=TrigramSimilarity(
                        Concat(
                            Coalesce("nombre", Value("")),
                            Value(" "),
                            Coalesce("apellido", Value("")),
                        ),
                        query_nombre,
                    ),
                )
                .filter(similarity__gt=0.15)
                .order_by("-similarity")
            )
        if query_institucion:
            institucion_query = (
                Universidad.objects.annotate(similarity=TrigramSimilarity("nombre", params.get("institucion")))
                .filter(similarity__gt=0.15)
                .order_by("-similarity")
            )
            qs = qs.filter(unidad__universidad__id__in=[i.id for i in institucion_query])
        if query_pais_code:
            qs = qs.filter(unidad__universidad__pais=query_pais_code)
        if query_area:
            ambitos_query = AmbitoTrabajo.objects.filter(subarea__area__nombre=query_area)
            qs = qs.filter(id__in=[a.academico.id for a in ambitos_query])
        if query_subarea:
            ambitos_query = AmbitoTrabajo.objects.filter(subarea__nombre=query_subarea)
            qs = qs.filter(id__in=[a.academico.id for a in ambitos_query])
        # if query_keyword:
        #     keyword_inv_query = KeywordInvestigador.objects.filter(keyword__nombre=query_keyword)
        #     qs = qs.filter(dblp_id__in=[a.investigador.dblp_id for a in keyword_inv_query])
        return qs

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademicoGetIdView(RetrieveAPIView):
    serializer_class = ApiAcademicoSerializer

    def get_object(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(AcademicoGetIdQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = AcademicoGetIdQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        academico_id = params.get("id")
        academico_id_dblp = params.get("dblp")
        academico_id_orcid = params.get("orcid")
        academico_obj = None
        if academico_id:
            academico_obj = Academico.objects.filter(id=academico_id).first()
        elif academico_id_dblp:
            try:
                dblp_obj = DblpProfile.objects.get(dblp_id=academico_id_dblp)
            except ObjectDoesNotExist:
                return None
            investigador = getattr(dblp_obj, "investigador_ondemand", None)
            academico_obj = getattr(investigador, "academico", None)
        elif academico_id_orcid:
            investigador = InvestigadorOnDemand.objects.filter(manual_orcid=academico_id_orcid).first()
            academico_obj = getattr(investigador, "academico", None)
            if not academico_obj:
                dblp_profile = DblpProfile.objects.filter(dblp_orcid_id=academico_id_orcid).first()
                investigador = getattr(dblp_profile, "investigador_ondemand", None)
                academico_obj = getattr(investigador, "academico", None)
            if not academico_obj:
                openalex_profile = OpenAlexProfile.objects.filter(orcid_id=academico_id_orcid).first()
                investigador = getattr(openalex_profile, "investigador_ondemand", None)
                academico_obj = getattr(investigador, "academico", None)
        return academico_obj

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstitucionSearchView(ListAPIView):
    serializer_class = ApiInstitutionSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(InstitucionQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = InstitucionQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        query_string = params.get("query", "")
        query_string_clean = query_string.lower()
        query_string_clean = query_string_clean.replace("universidad", "")
        query_string_clean = query_string_clean.replace("institucion", "")
        query_string_clean = query_string_clean.replace("institución", "")

        qs = (
            Universidad.objects.annotate(similarity=TrigramSimilarity("nombre", query_string_clean))
            .filter(similarity__gt=0.15)
            .order_by("-similarity")
        )
        qs_by_sigla = (
            Universidad.objects.annotate(similarity=TrigramSimilarity("sigla", query_string))
            .filter(similarity__gt=0.15)
            .exclude(id__in=[u.id for u in qs])
            .order_by("-similarity")
        )
        qs |= qs_by_sigla

        return qs

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstitucionGetIdView(RetrieveAPIView):
    serializer_class = ApiInstitutionSerializer

    def get_object(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(InstitucionGetIdQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = InstitucionGetIdQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data
        if params.get("id"):
            institucion_id = params.get("id")
            institucion_obj = Universidad.objects.get(id=institucion_id)

        elif params.get("openalex_id"):
            openalex_id = params.get("openalex_id")
            openalex_profile = OpenAlexInsitution.objects.filter(openalex_id=openalex_id).first()
            institucion_obj = getattr(openalex_profile, "universidad", None)

        elif params.get("ror_id"):
            ror_id = params.get("ror_id")
            if Universidad.objects.filter(id_ror=ror_id).exists():
                institucion_obj = Universidad.objects.filter(ror_id=ror_id).first()
            else:
                institucion_obj = OpenAlexInsitution.objects.filter(openalex_id_ror=ror_id).first()
                institucion_obj = getattr(institucion_obj, "universidad", None)

        return institucion_obj

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AreasListView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Area.objects.all()
    serializer_class = ApiAreaSerializer

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubareasByAreaView(ListAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Subarea.objects.all()
    serializer_class = ApiSubareaSerializer

    def get_queryset(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(SubareasByAreaQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = SubareasByAreaQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        area_id = params.get("id")
        subareas_query = Subarea.objects.filter(area__id=area_id)
        return subareas_query

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradoSearchView(ListAPIView):
    serializer_class = ApiGradoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(GradoSearchQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = GradoSearchQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        nombre = params.get("query", "")
        qs = GradoInstancia.objects.filter(is_deleted=False)
        if nombre:
            qs = (
                qs.annotate(
                    sim_nombre=TrigramSimilarity("nombre", nombre),
                    sim_nombre_es=TrigramSimilarity("nombre_es", nombre),
                )
                .annotate(similarity=Greatest("sim_nombre", "sim_nombre_es"))
                .filter(similarity__gt=0.15)
                .order_by("-similarity")
            )
        return qs

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradoSearchAdvancedView(ListAPIView):
    serializer_class = ApiGradoSerializer
    pagination_class = StandardResultsSetPagination
    serializer_class = ApiGradoSerializer

    def get_queryset(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = set(GradoAdvancedQuerySerializer().fields.keys())
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        qser = GradoAdvancedQuerySerializer(data=self.request.query_params)
        qser.is_valid(raise_exception=True)
        params = qser.validated_data

        nombre = params.get("nombre", "")
        universidad = params.get("universidad", "")
        tipo = params.get("tipo", "")
        qs = GradoInstancia.objects.filter(is_deleted=False)
        if nombre:
            qs = qs.annotate(
                sim_nombre=TrigramSimilarity("nombre", nombre),
                sim_nombre_es=TrigramSimilarity("nombre_es", nombre),
            ).annotate(similarity=Greatest("sim_nombre", "sim_nombre_es"))
            qs = qs.filter(similarity__gt=0.15).order_by("-similarity")
        if universidad:
            institucion_query = (
                Universidad.objects.annotate(similarity=TrigramSimilarity("nombre", universidad))
                .filter(similarity__gt=0.15)
                .order_by("-similarity")
            )
            qs = qs.filter(unidad__universidad__id__in=[i.id for i in institucion_query])
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs

    def list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradoGetIdView(RetrieveAPIView):
    serializer_class = ApiGradoSerializer

    def get_object(self):
        # strict query-param validation (allow 'page')
        incoming = set(self.request.query_params.keys())
        allowed = {"id"}
        extras = incoming - allowed
        if extras:
            raise DRFValidationError(
                {
                    "unknown_params": list(sorted(extras)),
                    "allowed_params": list(sorted(allowed)),
                }
            )
        id_val = self.request.query_params.get("id")
        if not id_val:
            raise DRFValidationError({"id": ["This field is required."]})
        try:
            grado_id = int(id_val)
        except (TypeError, ValueError):
            raise DRFValidationError({"id": ["A valid integer is required."]})
        g = GradoInstancia.objects.get(id=grado_id, is_deleted=False)
        return g

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except DRFValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
