import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from persona.models import Academico
from persona.services.aminer_client import update_investigador_aminer_data


class Command(BaseCommand):
    help = "Updates Aminer data for all academicos with aminer id."

    def handle(self, *args, **options):
        start_time = time.time()
        try:
            academicos_qs = (
                Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
                .filter(
                    # update after two weeks, just top 200 to avoid large porcesses
                    models.Q(investigador_ondemand__aminer_profile__isnull=False)
                    & models.Q(aminer_last_fetched_date__lt=timezone.now() - timezone.timedelta(weeks=2))
                )
                .distinct()[:50]
            )

            for i, academico in enumerate(academicos_qs):
                print(f"Processing Academico {i}/{len(academicos_qs)}: {academico.get_full_name()} (ID: {academico.id})")
                try:

                    with transaction.atomic():
                        inv, errors = update_investigador_aminer_data(academico, academico.investigador_ondemand.aminer_id)
                        if inv:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Updated investigador {academico.investigador_ondemand} with Aminer data {academico.investigador_ondemand.aminer_id}"
                                )
                            )
                        if errors:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Error updating investigador {academico.investigador_ondemand} for Academico {academico.get_full_name()}: {errors}"
                                )
                            )
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f"Error updating {academico.get_full_name()}: {e}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing Academico ID {academico.id}: {str(e)}"))
                finally:
                    academico.aminer_last_fetched_date = timezone.now()
                    academico.save()
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f"Aminer data fetch process completed in {elapsed_time:.2f} seconds"))
        except Exception as e:
            print(f"Error: {e}")
