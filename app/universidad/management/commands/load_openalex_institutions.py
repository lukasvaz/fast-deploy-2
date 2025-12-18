import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from universidad.models import OpenAlexInsitution, Universidad
from universidad.services.openalex_institution_client import BASE_URL, OpenAlexInstitutionSerializer


# Example URL:
# https://api.openalex.org/institutions?filter=continent:north_america|south_america,type:funder|education,country_code:!us|ca&page=4&per-page=200
class Command(BaseCommand):
    help = "Search OpenAlex for latin american institutions of type funder or education updates and creates new ones, handling pagination. Child will be omitted to avoid subinstitutions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting OpenAlex search for funder/education institutions..."))
        filter_str = "continent:north_america|south_america,type:funder|education,country_code:!us|ca"
        per_page = 200
        page = 1
        new_institutions_found = 0
        updated_institutions = 0
        skipped_institutions = 0

        while True:
            url = f"{BASE_URL}?filter={filter_str}&page={page}&per-page={per_page}"
            response = requests.get(url)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Failed to fetch page {page}: {response.text}"))
                break
            data = response.json()
            results = data.get("results", [])
            if not results:
                self.stdout.write(self.style.WARNING(f"No results on page {page}. Stopping."))
                break
            for inst in results:
                if len(inst.get("lineage")) > 1:
                    skipped_institutions += 1
                else:
                    serializer = OpenAlexInstitutionSerializer(data=inst)
                    if serializer.is_valid():
                        validated_data = serializer.validated_data
                        openalex_id = validated_data.get("openalex_id")
                        try:
                            # new institution, create Universidad if not exists and OpenalexInstitution
                            if openalex_id not in OpenAlexInsitution.objects.values_list("openalex_id", flat=True):
                                nombre = (
                                    validated_data.get("openalex_es_name")
                                    if validated_data.get("openalex_es_name")
                                    else validated_data.get("openalex_display_name")
                                )
                                sigla = validated_data.get("openalex_acronims")[0] if validated_data.get("openalex_acronims") else None
                                universidad, created = Universidad.objects.get_or_create(
                                    nombre=nombre, pais=validated_data.get("openalex_country_code"), sigla=sigla
                                )
                                if created:
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"Created new Universidad: {universidad.nombre} - {universidad.sigla} - {universidad.pais}"
                                        )
                                    )
                                validated_data.pop("openalex_country_code", None)
                                openalex_institution_obj = OpenAlexInsitution.objects.create(universidad=universidad, **validated_data)
                                for field, value in validated_data.items():
                                    if hasattr(openalex_institution_obj, field):
                                        setattr(openalex_institution_obj, field, value)
                                openalex_institution_obj.openalex_last_fetched_date = timezone.now()
                                openalex_institution_obj.save()
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"Created new Openalexinstitution: {openalex_id} - {validated_data.get('openalex_display_name')}"
                                    )
                                )
                                new_institutions_found += 1
                            # institution already exists, update data
                            else:
                                openalex_instance = OpenAlexInsitution.objects.get(openalex_id=openalex_id)
                                for field, value in validated_data.items():
                                    if hasattr(openalex_instance, field):
                                        setattr(openalex_instance, field, value)
                                openalex_instance.openalex_last_fetched_date = timezone.now()
                                openalex_instance.save()
                                updated_institutions += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"Error creating institution {openalex_id}: {str(e)} {validated_data.items()}")
                            )
            page += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. New institutions found: {new_institutions_found}, Institutions updated: {updated_institutions}, Skipped (child) institutions: {skipped_institutions}"
            )
        )
