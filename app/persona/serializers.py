# from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import (  # Grado,; EstudioUniversitario,
    Academico,
    AmbitoTrabajo,
    Area,
    Dominio,
    DominioAcademico,
    Subarea,
)

# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "url", "username", "email", "groups", "is_staff"]


# class GroupSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Group
#         fields = ["id", "url", "name"]


class InvestigadorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Academico
        fields = [
            "id",
            "url",
            "nombre",
            "apellido",
            "webpage",
            "email",
            "foto",
            "rol",
            "orcid",
            "linkedin",
        ]


class AcademicoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Academico
        fields = [
            "id",
            "url",
            "nombre",
            "apellido",
            "webpage",
            "email",
            "email_is_public",
            "foto",
            "rol",
            "orcid",
            "linkedin",
        ]


class DominioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dominio
        fields = [
            "id",
            "url",
            "nombre",
        ]


class DominioAcademicoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DominioAcademico
        fields = [
            "id",
            "url",
            "academico",
            "dominio",
        ]


class AreaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Area
        fields = [
            "id",
            "url",
            "nombre",
            "descripcion",
        ]


class SubareaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Subarea
        fields = [
            "id",
            "url",
            "area",
            "nombre",
            "descripcion",
        ]


class AmbitoTrabajoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AmbitoTrabajo
        fields = [
            "id",
            "url",
            "academico",
            "subarea",
            "activo",
        ]


# class GradoSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Grado
#         fields = [
#             "id",
#             "url",
#             "nombre",
#         ]


# class EstudioUniversitarioSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = EstudioUniversitario
#         fields = [
#             "id",
#             "url",
#             "grado",
#             "academico",
#             "descripcion",
#             "is_maximo",
#             "año",
#         ]
