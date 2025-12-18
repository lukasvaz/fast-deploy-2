from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from persona.models import Academico, AmbitoTrabajo


class Command(BaseCommand):
    help = "Compute summary stats for Academico objects (profiles, verification, pending)."

    def handle(self, *args, **options):
        total = Academico.objects.count()
        with_investigador = Academico.objects.filter(investigador_ondemand__isnull=False).count()

        # profiles existence (profile object) vs profile id (actual external id)
        with_aminer_profile = Academico.objects.filter(investigador_ondemand__aminer_profile__isnull=False).count()
        with_openalex_profile = Academico.objects.filter(investigador_ondemand__openalex_profile__isnull=False).count()
        with_dblp_profile = Academico.objects.filter(investigador_ondemand__dblp_profile__isnull=False).count()

        with_aminer_id = Academico.objects.filter(investigador_ondemand__aminer_profile__aminer_id__isnull=False).count()
        with_openalex_id = Academico.objects.filter(investigador_ondemand__openalex_profile__openalex_id__isnull=False).count()
        with_dblp_id = Academico.objects.filter(investigador_ondemand__dblp_profile__dblp_id__isnull=False).count()

        # verification / pending / unverified
        any_id_q = (
            Q(investigador_ondemand__aminer_profile__aminer_id__isnull=False)
            | Q(investigador_ondemand__openalex_profile__openalex_id__isnull=False)
            | Q(investigador_ondemand__dblp_profile__dblp_id__isnull=False)
        )
        verified = Academico.objects.filter(any_id_q).count()
        verification_pending = Academico.objects.filter(
            openalex_last_fetched_date__isnull=True, dblp_last_fetched_date__isnull=True, aminer_last_fetched_date__isnull=True
        ).count()
        unverified = Academico.objects.filter(~any_id_q).count()

        # breakdown: only one source present
        only_aminer = Academico.objects.filter(
            Q(investigador_ondemand__aminer_profile__aminer_id__isnull=False)
            & Q(investigador_ondemand__openalex_profile__openalex_id__isnull=True)
            & Q(investigador_ondemand__dblp_profile__dblp_id__isnull=True)
        ).count()
        only_openalex = Academico.objects.filter(
            Q(investigador_ondemand__openalex_profile__openalex_id__isnull=False)
            & Q(investigador_ondemand__aminer_profile__aminer_id__isnull=True)
            & Q(investigador_ondemand__dblp_profile__dblp_id__isnull=True)
        ).count()
        only_dblp = Academico.objects.filter(
            Q(investigador_ondemand__dblp_profile__dblp_id__isnull=False)
            & Q(investigador_ondemand__aminer_profile__aminer_id__isnull=True)
            & Q(investigador_ondemand__openalex_profile__openalex_id__isnull=True)
        ).count()

        multiple_sources = verified - (only_aminer + only_openalex + only_dblp)

        # academicos that have investigador_ondemand but none of the profile objects
        iod_no_profiles = Academico.objects.filter(
            investigador_ondemand__isnull=False,
            investigador_ondemand__aminer_profile__isnull=True,
            investigador_ondemand__openalex_profile__isnull=True,
            investigador_ondemand__dblp_profile__isnull=True,
        ).count()

        # print summary
        self.stdout.write(self.style.SUCCESS("Academicos summary"))
        self.stdout.write(f"  Total academicos: {total}")
        self.stdout.write(f"  With InvestigadorOnDemand object: {with_investigador}")
        self.stdout.write("")
        self.stdout.write("  Profiles (profile object present):")
        self.stdout.write(f"    Aminer profiles: {with_aminer_profile}")
        self.stdout.write(f"    OpenAlex profiles: {with_openalex_profile}")
        self.stdout.write(f"    DBLP profiles: {with_dblp_profile}")
        self.stdout.write("")
        self.stdout.write("  Profiles with external ID (actual verified id):")
        self.stdout.write(f"    Aminer id present: {with_aminer_id}")
        self.stdout.write(f"    OpenAlex id present: {with_openalex_id}")
        self.stdout.write(f"    DBLP id present: {with_dblp_id}")
        self.stdout.write("")
        self.stdout.write(f"  Verified (has at least one external id): {verified}")
        self.stdout.write(f"  Unverified (no external ids): {unverified}")
        self.stdout.write(f"  Verification pending (no fetches performed): {verification_pending}")
        self.stdout.write("")
        self.stdout.write("  Breakdown of sources (only one):")
        self.stdout.write(f"    Only Aminer: {only_aminer}")
        self.stdout.write(f"    Only OpenAlex: {only_openalex}")
        self.stdout.write(f"    Only DBLP: {only_dblp}")
        self.stdout.write(f"    Multiple sources: {multiple_sources}")
        self.stdout.write("")
        self.stdout.write(f"  InvestigadorOnDemand exists but no profile objects: {iod_no_profiles}")

        # compute AmbitoTrabajo distribution per Area
        area_counts = (
            AmbitoTrabajo.objects.values("subarea__area", "subarea__area__nombre")
            .annotate(academicos_count=Count("academico", distinct=True))
            .order_by("-academicos_count", "subarea__area__nombre")
        )

        total_ambito_academicos = AmbitoTrabajo.objects.values("academico").distinct().count()
        academicos_without_ambito = Academico.objects.exclude(id__in=AmbitoTrabajo.objects.values("academico")).count()

        self.stdout.write("")
        self.stdout.write("AmbitoTrabajo distribution per Area:")
        if total_ambito_academicos == 0:
            self.stdout.write("  (no AmbitoTrabajo entries found)")
        else:
            for row in area_counts:
                area_id = row.get("subarea__area")
                area_name = row.get("subarea__area__nombre") or f"(id={area_id})"
                count = row.get("academicos_count", 0)
                percent = (count / total_ambito_academicos) * 100 if total_ambito_academicos else 0
                self.stdout.write(f"  - {area_name} (id={area_id}): {count} academicos — {percent:.1f}%")

        self.stdout.write("")
        self.stdout.write(f"Academicos without any AmbitoTrabajo: {academicos_without_ambito}")

        self.stdout.write(self.style.SUCCESS("Done"))
