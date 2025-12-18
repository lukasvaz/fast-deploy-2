import requests
from rest_framework import serializers

BASE_URL = "https://api.openalex.org/institutions"


class OpenAlexInstitutionSerializer(serializers.Serializer):
    """
    Serializer for OpenAlex Institution data.Meant to use to map the JSON response from OpenAlex API to a Python/model representation.
    Fields match api fields names  and source match model fields names.
    """

    class GeoSerializer(serializers.Serializer):
        geonames_city_id = serializers.FloatField(source="openalex_city_id", required=False, allow_null=True)
        city = serializers.CharField(source="openalex_city_name", required=False, allow_null=True)
        latitude = serializers.FloatField(source="openalex_region_latitude", required=False, allow_null=True)
        longitude = serializers.CharField(source="openalex_region_longitude", required=False, allow_null=True)

    class InternationalSerializer(serializers.Serializer):
        class InternationalDisplayNameSerializer(serializers.Serializer):
            en = serializers.CharField(source="openalex_en_name", required=False, allow_null=True)
            es = serializers.CharField(source="openalex_es_name", required=False, allow_null=True)

        display_name = InternationalDisplayNameSerializer(required=False, allow_null=True)

    class IDSerializers(serializers.Serializer):
        ror = serializers.CharField(source="openalex_id_ror", required=False, allow_null=True)
        mag = serializers.CharField(source="openalex_id_mag", required=False, allow_null=True)
        grid = serializers.CharField(source="openalex_id_grid", required=False, allow_null=True)
        wikidata = serializers.CharField(source="openalex_id_wikidata", required=False, allow_null=True)
        wikipedia = serializers.CharField(source="openalex_id_wikipedia", required=False, allow_null=True)

        def validate_ror(self, value):
            if not value:
                return value
            return value.rstrip("/").split("/")[-1]

        def validate_wikidata(self, value):
            if not value:
                return value
            return value.rstrip("/").split("/")[-1]

    id = serializers.CharField(source="openalex_id", required=True)
    display_name = serializers.CharField(source="openalex_display_name", required=True)
    display_name_acronyms = serializers.ListField(
        source="openalex_acronims", child=serializers.CharField(), required=False, allow_null=True
    )
    display_name_alternatives = serializers.ListField(
        source="openalex_alternative_names", child=serializers.CharField(), required=False, allow_null=True
    )
    geo = GeoSerializer(required=False, allow_null=True)
    international = InternationalSerializer(required=False, allow_null=True)
    homepage_url = serializers.CharField(source="openalex_home_page_url", required=False, allow_null=True)
    image_thumbnail_url = serializers.CharField(source="openalex_thumbnail_url", required=False, allow_null=True)
    type = serializers.CharField(source="openalex_type", required=False, allow_null=True)
    ids = IDSerializers(required=False, allow_null=True)

    country_code = serializers.CharField(source="openalex_country_code", required=False, allow_null=True)

    def validate_id(self, value):
        return value.rstrip("/").split("/")[-1]

    def to_internal_value(self, data):
        """
        Overide to_internal_value to
        Flatten nested OpenAlex API response into flat model fields.
        """
        internal_data = super().to_internal_value(data)
        # Flatten nested structures
        if "geo" in data:
            internal_data["openalex_city_id"] = internal_data["geo"].get("openalex_city_id")
            internal_data["openalex_city_name"] = internal_data["geo"].get("openalex_city_name")
            internal_data["openalex_region_latitude"] = internal_data["geo"].get("openalex_region_latitude")
            internal_data["openalex_region_longitude"] = internal_data["geo"].get("openalex_region_longitude")
            internal_data.pop("geo", None)
        if "international" in data and "display_name" in data["international"]:
            internal_data["openalex_en_name"] = internal_data["international"]["display_name"].get("openalex_en_name")
            internal_data["openalex_es_name"] = internal_data["international"]["display_name"].get("openalex_es_name")
            internal_data.pop("international", None)
        if "ids" in data:
            internal_data["openalex_id_ror"] = internal_data["ids"].get("openalex_id_ror")
            internal_data["openalex_id_mag"] = internal_data["ids"].get("openalex_id_mag")
            internal_data["openalex_id_grid"] = internal_data["ids"].get("openalex_id_grid")
            internal_data["openalex_id_wikidata"] = internal_data["ids"].get("openalex_id_wikidata")
            internal_data["openalex_id_wikipedia"] = internal_data["ids"].get("openalex_id_wikipedia")
            internal_data.pop("ids", None)
        return internal_data


class OpenAlexInstitutionClient:
    """
    A client to interact with the OpenAlex Institutions API.
    """

    BASE_URL = BASE_URL

    def fetch_by_openalex_id(self, openalex_id):
        url = f"{self.BASE_URL}/{openalex_id}"
        json_response = self._get(url)
        serializer = OpenAlexInstitutionSerializer(data=json_response)
        serializer.is_valid(raise_exception=False)
        return serializer.validated_data

    def fetch_by_ror(self, ror_id):
        url = f"{self.BASE_URL}/ror:https://ror.org/{ror_id}"
        json_response = self._get(url)
        serializer = OpenAlexInstitutionSerializer(data=json_response)
        serializer.is_valid(raise_exception=False)
        return serializer.validated_data

    def fetch_by_wikidata(self, wikidata_id):
        url = f"{self.BASE_URL}/wikidata:{wikidata_id}"
        json_response = self._get(url)
        serializer = OpenAlexInstitutionSerializer(data=json_response)
        serializer.is_valid(raise_exception=False)
        return serializer.validated_data

    def fetch_by_name_and_country(self, name, country_code, sigla=None):
        response_data = []
        if sigla:
            url = f"{self.BASE_URL}?filter=country_code:{country_code},default.search:{sigla}"
            json_response = self._get(url)
            serializer = OpenAlexInstitutionSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
            if serializer.is_valid():
                response_data.append(serializer.validated_data)
        if len(response_data) == 0:
            url = f"{self.BASE_URL}?filter=country_code:{country_code},default.search:{name}"
            json_response = self._get(url)
            serializer = OpenAlexInstitutionSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
            if serializer.is_valid():
                response_data = serializer.validated_data
        return serializer.validated_data

    def fetch_by_name(self, name):
        url = f"{self.BASE_URL}?filter=default.search:{name}"
        json_response = self._get(url)
        serializer = OpenAlexInstitutionSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
        if serializer.is_valid():
            return serializer.validated_data
        return []

    def fetch_exact_insitution(self, universidad):
        """
        Dispatch method to fetch institution data based on available identifiers.
        Priority: openalex_id > ror_id > wikidata_id
        Input:
            universidad: An instance of the Universidad model.
        Output:
            -found: boolean indicating if an exact match was found.
            - A validated data dictionaries.
        """
        if getattr(universidad, "openalex_id", None):
            return True, self.fetch_by_openalex_id(universidad.openalex_id)

        elif getattr(universidad, "id_ror", None):
            result = self.fetch_by_ror(universidad.id_ror)
            if result.get("openalex_id"):
                return True, result

        elif getattr(universidad, "id_wikidata", None):
            result = self.fetch_by_wikidata(universidad.id_wikidata)
            if result.get("openalex_id"):
                return True, result
        return False, {}

    def fetch_suggested_institutions(self, universidad):
        """
        Suggest institutions based on name and country code and ids
        Input:
            universidad: An instance of the Universidad model.
        Output:
            A list of validated institution data dictionaries.
        """
        response = []
        # Each fetch returns a list, so extend instead of append
        if getattr(universidad, "openalex_institution", None):
            response.extend([self.fetch_by_openalex_id(universidad.openalex_institution.openalex_id)])
        if universidad.get_id_ror:
            response.extend([self.fetch_by_ror(universidad.get_id_ror)])
        if universidad.get_id_wikidata:
            response.extend([self.fetch_by_wikidata(universidad.get_id_wikidata)])
        response.extend(self.fetch_by_name_and_country(universidad.nombre, universidad.pais, getattr(universidad, "sigla", None)))
        response.extend(self.fetch_by_name(universidad.nombre))
        # Deduplicate by openalex_id
        seen = set()
        deduped = []
        for inst in response:
            oid = inst.get("openalex_id")
            if oid and oid not in seen:
                deduped.append(inst)
                seen.add(oid)
        return deduped

    def _get(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
