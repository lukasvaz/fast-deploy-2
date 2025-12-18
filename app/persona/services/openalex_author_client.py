import requests
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from persona.models import InvestigadorOnDemand, OpenAlexProfile

BASE_URL = "https://api.openalex.org/authors"


class OpenAlexAuthorsSerializer(serializers.Serializer):
    """
    Serializer for OpenAlex Institution data.Meant to use to map the JSON response from OpenAlex API to a Python/model representation.
    Fields match api fields names  and source match model fields names.
    """

    class IDSerializers(serializers.Serializer):
        orcid = serializers.CharField(source="openalex_id_orcid", required=False, allow_null=True)
        scopus = serializers.CharField(source="openalex_id_scopus", required=False, allow_null=True)
        wikipedia = serializers.CharField(source="openalex_id_wikipedia", required=False, allow_null=True)

        def validate_orcid(self, value):
            if not value:
                return value
            return value.rstrip("/").split("/")[-1]

    class LastKnownInstitutionSerializer(serializers.Serializer):
        id = serializers.CharField(required=True)
        ror = serializers.CharField(required=False, allow_null=True)
        display_name = serializers.CharField(required=True)

        def validate_id(self, value):
            if not value:
                return value
            return value.rstrip("/").split("/")[-1]

        def validate_ror(self, value):
            if not value:
                return value
            return value.rstrip("/").split("/")[-1]

    class TopicsSerializers(serializers.Serializer):
        display_name = serializers.CharField()
        count = serializers.IntegerField(required=False, allow_null=True)

    id = serializers.CharField(source="openalex_id", required=True)
    display_name = serializers.CharField(source="openalex_display_name", required=True)
    display_name_alternatives = serializers.ListField(
        source="openalex_alternative_names", child=serializers.CharField(), required=False, allow_null=True
    )
    works_count = serializers.IntegerField(source="openalex_works_count", required=False, allow_null=True)
    cited_by_count = serializers.IntegerField(source="openalex_cited_by_count", required=False, allow_null=True)
    ids = IDSerializers(required=False, allow_null=True)
    last_known_institutions = LastKnownInstitutionSerializer(
        source="openalex_last_known_institutions", many=True, required=False, allow_null=True
    )
    topics = TopicsSerializers(many=True, source="openalex_topics", required=False, allow_null=True)

    def validate_id(self, value):
        if not value:
            return value
        return value.rstrip("/").split("/")[-1]

    def to_internal_value(self, data):
        """
        Override to_internal_value to flatten nested OpenAlex API response into flat model fields.
        """
        internal_data = super().to_internal_value(data)
        # flatten ids
        if "ids" in data:
            ids = internal_data["ids"]
            internal_data["openalex_id_orcid"] = ids.get("openalex_id_orcid")
            internal_data["openalex_id_scopus"] = ids.get("openalex_id_scopus")
            internal_data["openalex_id_wikipedia"] = ids.get("openalex_id_wikipedia")
            internal_data.pop("ids", None)
        # Flatten last_known_institutions
        if "last_known_institutions" in data:
            institutions = []
            if internal_data["openalex_last_known_institutions"]:
                for inst in internal_data["openalex_last_known_institutions"]:
                    flat_inst = {
                        "institution_id": inst.get("id"),
                        "institution_ror": inst.get("ror"),
                        "institution_display_name": inst.get("display_name"),
                    }
                    institutions.append(flat_inst)
            internal_data["openalex_last_known_institutions"] = institutions
            internal_data.pop("last_known_institutions", None)
        if "topics" in data:
            internal_data["openalex_topics"] = {topic["display_name"]: topic.get("count", 0) for topic in internal_data["openalex_topics"]}
            internal_data.pop("topics", None)
        return internal_data


class OpenAlexAuthorClient:
    """
    A client to interact with the OpenAlex authors API.
    """

    BASE_URL = BASE_URL

    def fetch_by_openalex_id(self, openalex_id):
        url = f"{self.BASE_URL}/{openalex_id}"
        json_response = self._get(url)
        serializer = OpenAlexAuthorsSerializer(data=json_response)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            raise Exception(f"Error al validar datos de OpenAlex para ID {openalex_id}")
        return serializer.validated_data

    def fetch_by_orcid(self, ror_id):
        url = f"{self.BASE_URL}/orcid:{ror_id}"
        json_response = self._get(url)
        serializer = OpenAlexAuthorsSerializer(data=json_response)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def fetch_by_name_and_institution(self, name, institution=None):
        if institution and institution.openalex_id:
            url = f"{self.BASE_URL}?search={name}&filter=last_known_institutions.id:{institution.openalex_id}&sort=works_count:desc"
            json_response = self._get(url)
            serializer = OpenAlexAuthorsSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
            if serializer.is_valid(raise_exception=False):
                return serializer.validated_data
        elif institution and (institution.id_ror or getattr(institution, "openalex_institution", None)):
            ror = institution.id_ror or getattr(institution.openalex_institution, "openalex_id_ror", None)
            if ror:
                url = f"{self.BASE_URL}?filter=last_known_institutions.ror:{ror},display_name.search:{name}&sort=works_count:desc"
                json_response = self._get(url)
                serializer = OpenAlexAuthorsSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
                if serializer.is_valid(raise_exception=False):
                    return serializer.validated_data
        return []

    def fetch_by_name(self, name):
        url = f"{self.BASE_URL}?search={name}&sort=works_count:desc"
        json_response = self._get(url)
        serializer = OpenAlexAuthorsSerializer(data=json_response.get("results") if json_response.get("results") else [], many=True)
        if serializer.is_valid(raise_exception=False):
            return serializer.validated_data
        return []

    def fetch_exact_author(self, academico):
        """
        Dispatch method to fetch author data based on available identifiers.
        Priority: openalex_id > orcid_id
        Input:
            academico: An instance of Academico model.
        Output:
            -found: boolean indicating if an exact match was found.
            - A validated data dictionaries.
        """
        if getattr(academico, "investigador_ondemand.openalex_id", None):
            return True, self.fetch_by_openalex_id(academico.investigador_ondemand.openalex_id)
        elif getattr(academico, "orcid_id", None) or getattr(academico, "investigador_ondemand.openalex_id_orcid", None):
            orcid_id = academico.orcid_id if academico.orcid_id else academico.investigador_ondemand.openalex_id_orcid
            result = self.fetch_by_orcid(orcid_id)
            if result.get("openalex_id"):
                return True, result
        else:
            result = self.fetch_by_name_and_institution(academico.get_full_name(), academico.unidad.universidad)
            if len(result) > 0:
                return True, result[0]
        return False, {}

    def fetch_suggested_authors(self, academico):
        """
        Suggest authors based on author name and ids
        Input:
            academico: An instance of the Academico model.
        Output:
            A list of validated institution data dictionaries.
        """
        response = []
        # Each fetch returns a list, so extend instead of append
        if getattr(academico, "investigador_ondemand.openalex_profile", None):
            response.extend([self.fetch_by_openalex_id(academico.investigador_ondemand.openalex_id)])
        elif getattr(academico, "investigador_ondemand.get_orcid_id", None):
            orcid_id = academico.orcid_id if academico.orcid_id else academico.investigador_ondemand.openalex_id_orcid
            response.extend([self.fetch_by_orcid(orcid_id)])

        response.extend(self.fetch_by_name_and_institution(academico.get_full_name(), academico.unidad.universidad))
        response.extend(self.fetch_by_name(academico.get_full_name()))
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


def update_investigador_openalex_data(academico, openalex_id, is_manual=False, prefetched_data=None):
    """
    Fetch and update OpenAlex data for a given InvestigadorOnDemand instance based on a provided OpenAlex ID.Updates or creates the associated OpenAlexProfile.Updates AmbitoTrabajo for the linked Academico.
    Input:
        -investigador_obj: An instance of InvestigadorOnDemand model associated to an academico.
    Output:
        (InvestigadorOnDemand object, None) or (None,error dict )
    """
    client = OpenAlexAuthorClient()
    if prefetched_data and prefetched_data.get("openalex_id") == openalex_id and prefetched_data.get("openalex_display_name"):
        author_data = prefetched_data
    else:
        author_data = client.fetch_by_openalex_id(openalex_id)
    if author_data:
        # getting investigador
        if getattr(academico, "investigador_ondemand", None):
            investigador_obj = academico.investigador_ondemand
        else:
            investigador_obj = InvestigadorOnDemand(nombre=academico.nombre, apellido=academico.apellido, academico=academico)
            investigador_obj.save()

        profile_obj, created = OpenAlexProfile.objects.get_or_create(openalex_id=author_data.get("openalex_id"))
        # new profile
        if created:
            with transaction.atomic():
                for field, value in author_data.items():
                    if hasattr(profile_obj, field):
                        setattr(profile_obj, field, value)
                profile_obj.save()
                investigador_obj.openalex_profile = profile_obj
                investigador_obj.nombre = investigador_obj.academico.nombre
                investigador_obj.apellido = investigador_obj.academico.apellido
                investigador_obj.save()
        else:
            # if profile is linked to another investigador, reassign
            if InvestigadorOnDemand.objects.filter(openalex_profile=profile_obj).exclude(id=investigador_obj.id).exists():
                profile_obj.reassign_to(investigador_obj)
            else:
                investigador_obj.openalex_profile = profile_obj
                investigador_obj.save()

            for field, value in author_data.items():
                if hasattr(profile_obj, field):
                    setattr(profile_obj, field, value)
            profile_obj.save()
        investigador_obj.academico.openalex_last_fetched_date = timezone.now()
        investigador_obj.academico.save()
        return investigador_obj, None
    else:
        return None, {"error": "No se pudo encontrar un autor exacto en OpenAlex"}


def fetch_investigador_openalex_data(academico):
    """
    Fetch and update OpenAlex data for a given InvestigadorOnDemand instance based on its linked Academico.
    """
    client = OpenAlexAuthorClient()
    success, author_data = client.fetch_exact_author(academico)
    if success:
        inv, error = update_investigador_openalex_data(academico, author_data.get("openalex_id"), prefetched_data=author_data)
        if inv:
            return inv, None
        else:
            return None, error
    else:
        return None, {"error": "No se pudo encontrar un autor exacto en OpenAlex"}
