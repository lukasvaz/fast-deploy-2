from django.core.management import call_command
from django_cron import CronJobBase, Schedule


# ------ ACADEMICOS EXTERNAL DATA----------- #
class DblpFetchCronJob(CronJobBase):
    """fetch dblp data  for new academics"""

    # every day at 00000
    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["00:00"])
    # Identificador único para este CronJob
    code = "etl.dblp_update_cron_job"

    def do(self):
        try:
            print("DblpFetchCronJob running...")
            call_command("fetch_dblp_investigador_data")
        except Exception as e:
            print(f"Error running DblpFetchCronJob: {e}")


class DblpUpdateCronJob(CronJobBase):
    """updates dblp data for academics with dblp id"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["03:00"])
    code = "etl.dblp_investigator_update_cron_job"

    def do(self):
        try:
            print("DblpUpdateCronJob running...")
            call_command("update_dblp_investigadores")
        except Exception as e:
            print(f"Error: {e}")


class AminerFetchCronJob(CronJobBase):
    """fetch aminer data for new academics"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["00:00"])
    code = "etl.aminer_update_cron_job"

    def do(self):
        try:
            print("AminerFetchCronJob running...")
            call_command("fetch_aminer_data")
        except Exception as e:
            print(f"Error: {e}")


class AminerUpdateCronJob(CronJobBase):
    """updates aminer data for academics with aminer id"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["03:00"])
    code = "etl.aminer_investigator_update_cron_job"

    def do(self):
        try:
            print("AminerUpdateCronJob running...")
            call_command("update_aminer_investigadores")
        except Exception as e:
            print(f"Error: {e}")


class OpenAlexFetchCronJob(CronJobBase):
    """fetch openalex data for new academics"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["00:00"])
    code = "etl.openalex_authors_update_cron_job"

    def do(self):
        try:
            print("OpenAlexFetchCronJob running...")
            call_command("fetch_openalex_authors")
        except Exception as e:
            print(f"Error: {e}")


class OpenAlexUpdateCronJob(CronJobBase):
    """updates openalex data for academics with openalex id"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["03:00"])
    code = "etl.openalex_investigator_update_cron_job"

    def do(self):
        try:
            print("OpenAlexUpdateCronJob running...")
            call_command("update_openalex_investigadores")
        except Exception as e:
            print(f"Error: {e}")


class ValidateGradoUrlCronJob(CronJobBase):
    """validate grado url for all programas academicos"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["00:00"])
    # schedule = Schedule(run_every_mins=1)  # run every hour
    code = "etl.validate_grado_url_cron_job"

    def do(self):
        try:
            print("ValidateGradoUrlCronJob running...")
            call_command("validate_grado_url")
        except Exception as e:
            print(f"Error: {e}")


# ---------- Cleaning  data ---------#
class DeleteUnusedInvestigadorOnDemandCronJob(CronJobBase):
    """delete unused investigador on demand (not linked to any academico and not used in any coauthorship)"""

    schedule = Schedule(run_on_days=[0, 1, 2, 3, 4, 5, 6], run_at_times=["05:00"])
    code = "etl.delete_unused_investigadorondemand_cron_job"

    def do(self):
        try:
            print("DeleteUnusedInvestigadorOnDemandCronJob running...")
            call_command("delete_unused_investigadorondemand")
        except Exception as e:
            print(f"Error: {e}")
