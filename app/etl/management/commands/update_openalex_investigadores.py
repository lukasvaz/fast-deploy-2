import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from persona.models import Academico
from persona.services.openalex_author_client import update_investigador_openalex_data


class Command(BaseCommand):
    help = "Updates Openalex data for all academicos with openalex id."

    def handle(self, *args, **options):
        start_time = time.time()
        # update after two weeks, just top 200 to avoid large porcesses
        academicos_qs = (
            Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
            .filter(
                models.Q(investigador_ondemand__openalex_profile__isnull=False)
                & models.Q(openalex_last_fetched_date__lt=timezone.now() - timezone.timedelta(weeks=2))
            )
            .distinct()[:50]
        )
        total = 0
        failed = 0

        for i, a in enumerate(reversed(academicos_qs)):
            try:
                # Fetch OpenAlex data (sync function)
                print(
                    f"Updating OpenAlex data for Academico {i} {len(academicos_qs)}: {a.get_full_name()} {a.unidad.universidad} {a.unidad.universidad.openalex_id}"
                )
                with transaction.atomic():
                    inv, err = update_investigador_openalex_data(a, a.investigador_ondemand.openalex_id)
                    if inv:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated OpenAlex data for: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{a.investigador_ondemand.openalex_id}"
                            )
                        )
                    if err:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error updating OpenAlex data for: {a.get_full_name()} {a.unidad.universidad} with OpenAlex data https://openalex.org/{a.investigador_ondemand.openalex_id}: {err}"
                            )
                        )
                total += 1
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
        self.stdout.write(
            self.style.SUCCESS(
                f"Total Academicos updated with OpenAlex data: {total}, failed: {failed}, time taken: {elapsed_time:.2f} seconds"
            )
        )
