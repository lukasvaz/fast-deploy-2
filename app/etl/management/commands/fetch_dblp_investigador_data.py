import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from persona.models import Academico
from persona.services.dblp_client import DblpTimeOutError, fetch_investigador_dblp_data


class Command(BaseCommand):
    help = "Fetch and update missing DBLP IDs for Academico entries."

    def handle(self, *args, **options):
        start_time = time.time()
        total = 0
        academicos_qs = (
            Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
            .filter(
                (
                    #  academicos sin investigador asociado
                    models.Q(investigador_ondemand__isnull=True)
                    & models.Q(dblp_last_fetched_date__isnull=True)
                )
                | (
                    # academicos sin perfil dblp asociado
                    models.Q(investigador_ondemand__dblp_profile__isnull=True)
                    & models.Q(dblp_last_fetched_date__isnull=True)
                )
            )
            .distinct()
        )
        # for failed retry after two weeks, limit to 200 to avoid large processes
        academicos_retry_qs = (
            Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
            .filter(
                models.Q(investigador_ondemand__dblp_profile__isnull=True)
                & models.Q(dblp_last_fetched_date__lt=timezone.now() - timezone.timedelta(weeks=2))
            )
            .order_by("id")[:50]
        )
        academicos_qs = list(academicos_qs) + list(academicos_retry_qs)
        for i, a in enumerate(academicos_qs):
            print(f"Processing Academico {i}/{len(academicos_qs)}: {a.get_full_name()} (ID: {a.id})")
            try:
                with transaction.atomic():
                    ob, error = fetch_investigador_dblp_data(academico=a)
                    if ob:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated InvestigadorOnDemand {a.investigador_ondemand.nombre} with DBLP data for Academico {a.get_full_name()}"
                            )
                        )
                    if error:
                        self.stdout.write(
                            self.style.ERROR(f"Error updating InvestigadorOnDemand for Academico {a.get_full_name()}: {error}")
                        )
                    total += 1
                a.dblp_last_fetched_date = timezone.now()
                a.save()
            except DblpTimeOutError as e:  # if api is down not marked as fetched
                self.stdout.write(
                    self.style.ERROR(f"Timeout error fetching DBLP data for Academico ID {a.id}: {str(e)}, API  is probably down")
                )
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Error updating {a.get_full_name()}: {e}"))
                a.dblp_last_fetched_date = timezone.now()
                a.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing Academico ID {a.id}: {str(e)}"))
                a.dblp_last_fetched_date = timezone.now()
                a.save()
        elapsed_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Total Academicos without investigador_ondemand or without dblp_id: {total}, time taken: {elapsed_time:.2f} seconds"
            )
        )
