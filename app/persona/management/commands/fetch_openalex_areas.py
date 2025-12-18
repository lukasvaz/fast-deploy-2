import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from persona.models import Area, Keyword, Subarea

URL = "https://api.openalex.org/fields/17"


class Command(BaseCommand):
    help = "Fetch OpenAlex given an openalexURLFIeld creates Area/Subarea/Keyword records in DB.Matches Subfield with Area, Topics with Subarea, Keywords with Keyword."

    def handle(self, *args, **options):
        try:
            headers = {"User-Agent": "repositorio-acad-micos-fetch/1.0"}
            resp = requests.get(URL, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise CommandError(f"Error fetching OpenAlex fields: {e}")

        if not isinstance(data, dict) or "subfields" not in data or not isinstance(data["subfields"], list):
            raise CommandError("Unexpected OpenAlex response: expected top-level 'subfields' list")

        created_areas = 0
        created_subareas = 0
        created_keywords = 0
        topics_processed = 0

        for idx, subfield_obj in enumerate(data["subfields"]):
            display_name = subfield_obj.get("display_name") or subfield_obj.get("id") or f"field_{idx}"
            raw_id = subfield_obj.get("id", "")
            last_seg = raw_id.rstrip("/").split("/")[-1] if raw_id else ""
            self.stdout.write(f"Processing field {idx+1}/{len(data['subfields'])}: {display_name}")

            # fetch detailed field info
            try:
                field_resp = requests.get(f"https://api.openalex.org/subfields/{last_seg}", headers=headers, timeout=30)
                field_resp.raise_for_status()
                detailed_field = field_resp.json()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - failed to fetch detailed field {display_name}: {e}"))
                continue
            description = detailed_field.get("description") or ""

            with transaction.atomic():
                area_obj, area_created = Area.objects.get_or_create(
                    nombre=display_name,
                    defaults={"descripcion": description or ""},
                )
                if area_created:
                    created_areas += 1

                # topics/subfields under this field
                topics = detailed_field.get("topics") or detailed_field.get("subfields") or []

                for t in topics:
                    topics_processed += 1
                    topic_name = t.get("display_name") or t.get("id") or f"topic_{topics_processed}"
                    topic_raw_id = (t.get("id") or "").rstrip("/").split("/")[-1] if t.get("id") else ""

                    sub_obj, sub_created = Subarea.objects.get_or_create(
                        area=area_obj,
                        nombre=topic_name,
                        defaults={"descripcion": ""},
                    )
                    if sub_created:
                        created_subareas += 1

                    # try fetching topic detail to obtain keywords
                    keywords = []
                    if topic_raw_id:
                        try:
                            t_resp = requests.get(f"https://api.openalex.org/{topic_raw_id}", headers=headers, timeout=30)
                            t_resp.raise_for_status()
                            topic_detailed = t_resp.json()
                            description = topic_detailed.get("description").replace("This cluster of papers ", "") or ""
                            sub_obj.descripcion = description[:1].upper() + description[1:]
                            sub_obj.save()
                            keywords = topic_detailed.get("keywords") or []

                        except Exception:
                            keywords = []

                    for kw in keywords:
                        if not kw:
                            continue
                        kw_name = kw.strip() if isinstance(kw, str) else str(kw)
                        key_obj, key_created = Keyword.objects.get_or_create(nombre=kw_name)
                        if key_created:
                            created_keywords += 1
                        # associate keyword with subarea if not already
                        if not key_obj.subarea.filter(pk=sub_obj.pk).exists():
                            key_obj.subarea.add(sub_obj)

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished: areas_created={created_areas}, subareas_created={created_subareas}, keywords_created={created_keywords}, topics_processed={topics_processed}"
            )
        )
