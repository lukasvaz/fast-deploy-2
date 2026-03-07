import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from persona.models import Academico
from persona.services.aminer_client import fetch_investigador_aminer_data


class Command(BaseCommand):
    help = "Fetch data from Aminer for all academicos. By default fetches new academicos and retries failed ones. Use --new-only to fetch only new academicos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--new-only",
            action="store_true",
            dest="new_only",
            help="Fetch only new academicos (skip retry of failed). By default fetches new academicos and retries failed ones.",
        )

    def handle(self, *args, **options):
        start_time = time.time()
        try:
            new_academicos_qs = (
                # order by id
                Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
                .filter(
                    (
                        models.Q(is_deleted=False)
                        & models.Q(investigador_ondemand__isnull=True)
                        & models.Q(aminer_last_fetched_date__isnull=True)
                    )
                    | (
                        models.Q(is_deleted=False)
                        & models.Q(investigador_ondemand__aminer_profile__isnull=True)
                        & models.Q(aminer_last_fetched_date__isnull=True)
                    )
                )
                .distinct()
            )
            retry_academicos_qs = (
                Academico.objects.select_related("unidad__universidad", "investigador_ondemand")
                .filter(
                    # for failed retry after two weeks, just top 200 to avoid large porcesses
                    models.Q(investigador_ondemand__aminer_profile__isnull=True)
                    & models.Q(aminer_last_fetched_date__lt=timezone.now() - timezone.timedelta(weeks=2))
                )
                .order_by("id")[:50]
            )

            # choose mode: by default fetch both new and retry sets; when --new-only is provided fetch only new academicos
            new_only = options.get("new_only", False)
            if new_only:
                academicos_qs = list(new_academicos_qs)
            else:
                academicos_qs = list(new_academicos_qs) + list(retry_academicos_qs)

            for i, academico in enumerate(academicos_qs):
                print(
                    f"Fetching Aminer for Academico {i}/{len(academicos_qs)}: {academico.get_full_name()} -{academico.unidad.universidad} (ID: {academico.id})"
                )
                try:
                    # if academico.investigador_ondemand:
                    with transaction.atomic():
                        inv, errors = fetch_investigador_aminer_data(academico)
                        if not errors:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Updated investigador {academico.investigador_ondemand} with Aminer data {academico.investigador_ondemand.aminer_id}"
                                )
                            )
                        else:
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
