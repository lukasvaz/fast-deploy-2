from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from universidad.models import OpenAlexInsitution, Universidad
from universidad.services.openalex_institution_client import OpenAlexInstitutionClient


class Command(BaseCommand):
    help = "Fetch OpenAlex data for universities using other identifiers."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting OpenAlex ID search..."))
        total_updated = 0
        total_failed = 0
        universidades_to_update = Universidad.objects.filter(
            (Q(openalex_institution__isnull=True) & (Q(id_wikidata__isnull=False) | Q(id_ror__isnull=False)))
        )
        for universidad in universidades_to_update:
            openalex_client = OpenAlexInstitutionClient()
            try:
                success, openalex_data = openalex_client.fetch_exact_insitution(universidad)
                if success:
                    universidad = Universidad.objects.get(nombre=universidad.nombre, sigla=universidad.sigla, pais=universidad.pais)
                    self.stdout.write(f"Updating OpenAlex data for: {universidad.nombre} - {universidad.sigla} - {universidad.pais}")
                    openalex_instance, created = OpenAlexInsitution.objects.get_or_create(
                        openalex_id=openalex_data.get("openalex_id"), universidad=universidad
                    )
                    # updates all openalex fields in universidad instance
                    for field, value in openalex_data.items():
                        if hasattr(openalex_instance, field):
                            setattr(openalex_instance, field, value)
                    openalex_instance.openalex_last_fetched_date = timezone.now()
                    openalex_instance.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated OpenAlex data for: {universidad.nombre} - {universidad.sigla} - {universidad.pais}")
                    )
                    total_updated += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error fetching data for {universidad.nombre}: {str(e)}"))
                total_failed += 1
            pass

        self.stdout.write(self.style.SUCCESS(f"OpenAlex ID search completed. Total updated: {total_updated}, Total failed: {total_failed}"))
