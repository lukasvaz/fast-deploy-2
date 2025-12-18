from django.core.management.base import BaseCommand
from persona.models import Academico, InvestigadorOnDemand
from persona.services.aminer_client import fetch_investigador_aminer_data
from django.db import models
import time
from django.db import transaction
from django.utils import timezone
from django.db import IntegrityError

class Command(BaseCommand):
    help = "Fetch data from Aminer for all academicos."

    def handle(self, *args, **options):
        start_time = time.time()
        try:
            academicos_qs = Academico.objects.select_related('unidad__universidad', 'investigador_ondemand').filter(
            (   
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__isnull=True) &
                models.Q(aminer_last_fetched_date__isnull=True)
            ) |
            (
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__aminer_profile__isnull=True) &
                models.Q(aminer_last_fetched_date__isnull=True)
            )
            ).distinct()
            # academicos_qs = Academico.objects.all().order_by('id')[830::]

            for i,academico in enumerate(academicos_qs):
                    try:
                        print(f"Processing Academico {i}/{len(academicos_qs)}: {academico.get_full_name()} (ID: {academico.id})")
                        if academico.investigador_ondemand:
                            with transaction.atomic():
                                inv,errors=fetch_investigador_aminer_data(academico.investigador_ondemand)    
                                if inv:
                                    self.stdout.write(self.style.SUCCESS(f"Updated investigador {academico.investigador_ondemand} with Aminer data {academico.investigador_ondemand.aminer_id}"))
                                if errors:
                                    self.stdout.write(self.style.ERROR(f"Errors updating {academico.get_full_name()}: {errors}"))
                                
                        else: 
                            with transaction.atomic():
                                investigador_new=InvestigadorOnDemand(academico=academico)
                                inv,errors=fetch_investigador_aminer_data(investigador_new)    
                                if inv:
                                    academico.investigador_ondemand = inv
                                    academico.save()
                                    self.stdout.write(self.style.SUCCESS(f"Created and linked new investigador {investigador_new} with Aminer data {investigador_new.aminer_id}"))
                                if errors:
                                    self.stdout.write(self.style.ERROR(f"Errors creating investigador for {academico.get_full_name()}: {errors}"))
                            
                    except IntegrityError as e:
                            self.stdout.write(self.style.ERROR(f"Error updating {academico.get_full_name()}: {e}"))
                    except UnicodeEncodeError as e:
                            academico.investigador_ondemand = None
                            self.stdout.write(self.style.ERROR(f"UnicodeEncodeError for {academico.get_full_name()}: {str(e)}"))
                    except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error processing Academico ID {academico.id}: {str(e)}"))
                    finally:
                        academico.aminer_last_fetched_date = timezone.now()
                        academico.save()
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f"Aminer data fetch process completed in {elapsed_time:.2f} seconds"))
        except Exception as e:
            print(f"Error: {e}")
