from django.core.management.base import BaseCommand

from universidad.models import Universidad


class Command(BaseCommand):
    help = "Hard delete all institutions where is_deleted=True"

    def handle(self, *args, **options):
        institutions = Universidad.objects.filter(is_deleted=True)

        total = institutions.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No institutions with is_deleted=True found."))
            return

        for inst in institutions:
            self.stdout.write(f"Deleting: {inst} (ID: {inst.id})")
            inst.unidades_set.filter(is_deleted=True).delete()
            inst.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {total} institutions with is_deleted=True."))
