from rest_framework import serializers

from .models import Unidad, Universidad


class UniversidadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Universidad
        fields = [
            "id",
            "url",
            "nombre",
            "sigla",
            "webpage",
            "pais",
            "casa_central",
            "foto_escudo",
            "foto_banner",
            "is_manual",
            "is_cruch",
            "id_ringgold",
            "id_wikidata",
            "id_ror",
            "id_isni",
            "id_crossref",
        ]


class UnidadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Unidad
        fields = [
            "id",
            "url",
            "universidad",
            "nombre",
            "sigla",
            "webpage",
            "foto",
            "is_manual",
        ]


# class UniversidadSerializer(serializers.Serializer):
# id = serializers.IntegerField(read_only=True)
# nombre = serializers.CharField(
#     required=True, allow_blank=False, max_length=200
# )
# sigla = serializers.CharField(
#     required=False, allow_blank=True, max_length=10
# )
# webpage = serializers.URLField(required=False)
# pais = serializers.CharField(
#     required=True, allow_blank=False, max_length=200
# )
# foto_escudo = serializers.FileField(
#     upload_to="uploads/", required=False, allow_blank=True
# )
# foto_banner = serializers.FileField(
#     upload_to="uploads/", required=False, allow_blank=True
# )

# def create(self, validated_data):
#     return Universidad.objects.create(**validated_data)

# def update(self, instance, validated_data):
#     instance.nombre = validated_data.get("nombre", instance.nombre)
#     instance.sigla = validated_data.get("sigla", instance.sigla)
#     instance.webpage = validated_data.get("webpage", instance.webpage)
#     instance.save()
#     return instance
