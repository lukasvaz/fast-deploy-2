from django.core.management.base import BaseCommand
from persona.models import Academico, InvestigadorOnDemand
from persona.services.openalex_author_client import OpenAlexAuthorClient,fetch_investigador_openalex_data
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.db import IntegrityError
import time

class Command(BaseCommand):
    help = "Fetch OpenAlex data for all Academicos without investigador or without openalex_id"

    def handle(self, *args, **options):
        start_time = time.time()
        academicos_qs = Academico.objects.select_related('unidad__universidad', 'investigador_ondemand').filter(
            (   
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__isnull=True) &
                models.Q(openalex_last_fetched_date__isnull=True)
            ) |
            (
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__openalex_profile__isnull=True) &
                models.Q(openalex_last_fetched_date__isnull=True)
            )
        ).distinct()
        total = 0
        failed = 0
        client=OpenAlexAuthorClient()
        
        for i,a in enumerate(reversed(academicos_qs)):
            try:
                # Fetch OpenAlex data (sync function)
                print(f"Fetching OpenAlex data for Academico {i} {len(academicos_qs)}: {a.get_full_name()} {a.unidad.universidad} {a.unidad.universidad.openalex_id}")
                success,author_data=client.fetch_exact_author(a)
                if success:
                    if not a.investigador_ondemand:
                        with transaction.atomic():
                                investigador_on_demand = InvestigadorOnDemand()
                                investigador_on_demand.academico = a
                                inv,err=fetch_investigador_openalex_data(investigador_on_demand)
                                if inv:
                                    a.investigador_ondemand = inv
                                    a.save()
                                    self.stdout.write(self.style.SUCCESS(f"Created InvestigadorOnDemand and linked to Academico: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{investigador_on_demand.openalex_id}"))
                                if err:
                                    self.stdout.write(self.style.ERROR(f"Error creating InvestigadorOnDemand for: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{investigador_on_demand.openalex_id}: {err}"))
                    else:
                        with transaction.atomic():
                            investigador_on_demand = a.investigador_ondemand
                            inv,err=fetch_investigador_openalex_data(investigador_on_demand)
                            if inv:
                                self.stdout.write(self.style.SUCCESS(f"Updated OpenAlex data for: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{investigador_on_demand.openalex_id}"))
                            if err:
                                self.stdout.write(self.style.ERROR(f"Error updating OpenAlex data for: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{investigador_on_demand.openalex_id}: {err}"))
                    total += 1
                else:
                    failed += 1
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Error processing Academico ID {a.id}: {str(e)}"))
                failed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing Academico ID {a.id}: {str(e)}"))
                failed += 1
            finally:
                a.openalex_last_fetched_date = timezone.now()
                a.save()
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Total Academicos updated with OpenAlex data: {total}, failed: {failed}, time taken: {elapsed_time:.2f} seconds"))