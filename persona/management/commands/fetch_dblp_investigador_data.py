from django.core.management.base import BaseCommand
from persona.models import Academico, InvestigadorOnDemand,CoautorInvestigador
from persona.services.dblp_client import fetch_investigador_dblp_data,DblpTimeOutError
from django.db import transaction
from django.db import models
from django.utils import timezone
from django.db import IntegrityError
import time

class Command(BaseCommand):
    help = "Fetch and update missing DBLP IDs for Academico entries."

    def handle(self, *args, **options):
        start_time = time.time()
        total=0
        academicos_qs = Academico.objects.select_related('unidad__universidad', 'investigador_ondemand').filter(
            (   
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__isnull=True) &
                models.Q(dblp_last_fetched_date__isnull=True)
            ) |
            (
                models.Q(is_deleted=False) &
                models.Q(investigador_ondemand__dblp_profile__isnull=True) &
                models.Q(dblp_last_fetched_date__isnull=True)
            )
        ).distinct()
        # academicos without dblp profile
        # academicos_qs = Academico.objects.select_related('unidad__universidad', 'investigador_ondemand').filter(
        #     models.Q(is_deleted=False) &
        #     (
        #         models.Q(investigador_ondemand__isnull=True) |
        #         models.Q(investigador_ondemand__dblp_profile__isnull=True)
        #     )
        # ).distinct().order_by('id')[60:100]

        for i,a in enumerate(academicos_qs):
                    print(f"Processing Academico {i}/{len(academicos_qs)}: {a.get_full_name()} (ID: {a.id})")
                    try:
                            with transaction.atomic():
                                if a.investigador_ondemand:
                                    ob,error=fetch_investigador_dblp_data(a.investigador_ondemand)
                                    if ob:
                                        self.stdout.write(self.style.SUCCESS(f"Updated InvestigadorOnDemand {a.investigador_ondemand.nombre} with DBLP data for Academico {a.get_full_name()}"))
                                    if error:
                                        self.stdout.write(self.style.ERROR(f"Error updating DBLP data for Academico ID {a.id}: {error}"))
                                    
                                    total+=1
                                if not a.investigador_ondemand:
                                    with transaction.atomic():
                                        investigador_obj=InvestigadorOnDemand(academico=a)
                                        ob,error=fetch_investigador_dblp_data(investigador_obj=investigador_obj)
                                        if ob:
                                            if not ob.pk:
                                                ob.save()
                                            a.investigador_ondemand=ob
                                            a.save()
                                            self.stdout.write(self.style.SUCCESS(f"Created InvestigadorOnDemand {a.investigador_ondemand.nombre} with  for Academico {a.get_full_name()}"))
                                            total+=1
                                        if error:
                                            a.investigador_ondemand = None
                                            a.save()
                                            self.stdout.write(self.style.ERROR(f"Error creating DBLP data for Academico ID {a.id}: {error}"))

                    except DblpTimeOutError as e: # if api is down not marked as fetched
                        self.stdout.write(self.style.ERROR(f"Timeout error fetching DBLP data for Academico ID {a.id}: {str(e)}, API  is probably down"))
                    except IntegrityError as e:
                        self.stdout.write(self.style.ERROR(f"Error updating {a.get_full_name()}: {e}"))
                        a.dblp_last_fetched_date = timezone.now()
                        a.save()    
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing Academico ID {a.id}: {str(e)}"))
                        a.dblp_last_fetched_date = timezone.now()
                        a.save()    
                    time.sleep(1)  # To avoid hitting API rate limits
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Total Academicos without investigador_ondemand or without dblp_id: {total}, time taken: {elapsed_time:.2f} seconds"))

