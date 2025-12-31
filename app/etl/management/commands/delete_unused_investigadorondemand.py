from django.core.management.base import BaseCommand

from persona.models import (
    Academico,
    AminerProfile,
    CoautorInvestigador,
    DblpProfile,
    InvestigadorCandidato,
    InvestigadorOnDemand,
    OpenAlexProfile,
    Keyword,
    KeywordInvestigador
)


class Command(BaseCommand):
    help = "Delete all InvestigadorOnDemand not used in CoautorInvestigador (a or b) and not pointed by any Academico."

    def handle(self, *args, **options):
        used_in_coauthors = set(CoautorInvestigador.objects.values_list("investigador_a_id", flat=True)) | set(
            CoautorInvestigador.objects.values_list("investigador_b_id", flat=True)
        )
        used_by_academico = set(
            Academico.objects.filter(investigador_ondemand__isnull=False).values_list("investigador_ondemand_id", flat=True)
        )

        used_ids = used_in_coauthors | used_by_academico

        unused_investigadores = InvestigadorOnDemand.objects.exclude(id__in=used_ids).order_by("created_date")
        count = unused_investigadores.count()

        if count > 0:
            ids = list(unused_investigadores.values_list("id", flat=True))
            self.stdout.write(f"Deleting {count} unused InvestigadorOnDemand (IDs: {ids})...")
            deleted_count, _ = unused_investigadores.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} InvestigadorOnDemand objects."))
        else:
            self.stdout.write(self.style.NOTICE("No unused InvestigadorOnDemand to delete."))

        # also delete remaining orphan profiles
        # DblpProfile
        dblp_orphans = DblpProfile.objects.filter(investigador_ondemand__isnull=True)
        count_dblp = dblp_orphans.count()
        if count_dblp:
            self.stdout.write(f"Deleting {count_dblp} orphan DblpProfile(s)...")
            dblp_orphans.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count_dblp} DblpProfile(s)"))
        else:
            self.stdout.write(self.style.NOTICE("No orphan DblpProfile found."))

        # AminerProfile
        aminer_orphans = AminerProfile.objects.filter(investigador_ondemand__isnull=True)
        count_aminer = aminer_orphans.count()
        if count_aminer:
            self.stdout.write(f"Deleting {count_aminer} orphan AminerProfile(s)...")
            aminer_orphans.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count_aminer} AminerProfile(s)"))
        else:
            self.stdout.write(self.style.NOTICE("No orphan AminerProfile found."))

        # OpenAlexProfile
        openalex_orphans = OpenAlexProfile.objects.filter(investigador_ondemand__isnull=True)
        count_openalex = openalex_orphans.count()
        if count_openalex:
            self.stdout.write(f"Deleting {count_openalex} orphan OpenAlexProfile(s)...")
            openalex_orphans.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count_openalex} OpenAlexProfile(s)"))
        else:
            self.stdout.write(self.style.NOTICE("No orphan OpenAlexProfile found."))

        # investigadorCandidato
        # Find all InvestigadorCandidato objects where candidatos is empty
        empty_candidates = InvestigadorCandidato.objects.filter(candidatos=[])
        count = empty_candidates.count()
        if count == 0:
            self.stdout.write(self.style.NOTICE("No InvestigadorCandidato with empty candidatos found."))
        else:
            deleted_count, _ = empty_candidates.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {deleted_count} InvestigadorCandidato(s)."))
        
        # delete all keywords not linked to any keywordinvestigador
        total_keywords = Keyword.objects.count()
        unused_keywords = Keyword.objects.exclude(
            id__in=KeywordInvestigador.objects.values_list("keyword_id", flat=True)
        )

        count_keywords = unused_keywords.count()        
        if count_keywords:
            unused_keywords.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count_keywords} Keyword(s)"))
        else:
            self.stdout.write(self.style.NOTICE("No unused Keyword found."))
        # delete all keywordInvestigador without investigador_ondemand.aminer profile or investigador_ondemand
        #investigadores without aminer profile 
        invs_ids=InvestigadorOnDemand.objects.filter(aminer_profile__isnull=True).values_list('id',flat=True)
    
        orphan_keyword_investigador = KeywordInvestigador.objects.filter(
            investigador__in=invs_ids
        )
        print(invs_ids)
        print(orphan_keyword_investigador)
        count_ki = orphan_keyword_investigador.count()
        if count_ki:
            orphan_keyword_investigador.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count_ki} orphan KeywordInvestigador(s)"))
        else:
            self.stdout.write(self.style.NOTICE("No orphan KeywordInvestigador found."))
        