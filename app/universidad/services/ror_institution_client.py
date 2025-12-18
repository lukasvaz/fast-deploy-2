import requests
from rest_framework import serializers

BASE_URL = "https://api.ror.org/organizations"


class RorInstitutionSerializer(serializers.Serializer):
    class geoInfoserializers(serializers.Serializer):
        geonames_details = serializers.DictField(source="ror_geo_details", required=False, allow_null=True)

    class namesSerializer(serializers.Serializer):
        lang = serializers.CharField(source="ror_name_lang", required=False, allow_null=True)
        value = serializers.CharField(source="ror_name_value", required=False, allow_null=True)

    id = serializers.CharField(source="ror_id")
    names = serializers.ListField(source="ror_names", child=namesSerializer(), required=False, allow_null=True)
    locations = geoInfoserializers(required=False, source="ror_locations", allow_null=True, many=True)

    def validate_id(self, value):
        return value.rstrip("/").split("/")[-1]


class RorInstitutionClient:
    BASE_URL = BASE_URL

    def fetch_by_name(self, institution):
        """
        Fetch institution data from ROR API by ROR ID.
        Returns a dict with at least the ROR id (always the short id, e.g. '042nb2s44').
        """
        url = f"{self.BASE_URL}?query={institution.nombre}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            # Only keep the short id
            # print(data['items'])
            serializer = RorInstitutionSerializer(data=data["items"], many=True)
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data
        except Exception as e:
            return {"error": str(e)}
