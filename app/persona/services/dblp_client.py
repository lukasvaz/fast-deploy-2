import html
from datetime import date

import httpx
import requests
from django.db import DataError, Error, IntegrityError, models
from django.utils import timezone
from httpx import TimeoutException
from requests import Timeout

from persona.models import Academico, CoautorInvestigador, DblpProfile, InvestigadorOnDemand


class DblpTimeOutError(Exception):
    """Exception raised for timeout errors when accessing DBLP."""

    def __init__(self, message="Timeout occurred while accessing DBLP."):
        self.message = message
        super().__init__(self.message)


# Get Data from dblp
def dblp_get_data(dblp_id):
    url = f"https://dblp.org/pid/{dblp_id}.xml"
    try:
        investigador_data = requests.get(
            url=url,
            timeout=30,
        )
    except Timeout:
        raise DblpTimeOutError(f"Timeout error while accessing DBLP for ID: {dblp_id}")
    if investigador_data.status_code != 200:
        return None
    else:
        data = investigador_data.text.split("\n")
        #  Read every line fetching data (ignore <coauthors ...>)
        #  type_line
        #  "person"       -> <person ...>...</person>
        #  "conference"   -> <r><inproceedings ...>...</inproceedings></r>  (conference)
        #  "conference"   -> <r><proceedings ...>...</proceedings></r>      (conference)
        #  "article"      -> <r><article ...>...</article></r>              (journals)
        n_conferences = 0
        n_journals = 0
        names = []
        urls = []
        coauthor = {}
        orcid_id = []
        last_publ_year = 1900

        type_line = ""

        for line in data:
            #  This if search for person/conference/article
            if type_line == "":
                if "<person " in line:
                    type_line = "person"
                    continue
                elif "<inproceedings " in line:
                    n_conferences += 1
                    type_line = "conference"
                    continue
                elif "<article " in line and 'publtype="informal"' not in line:
                    n_journals += 1
                    type_line = "article"
                    continue
                elif "<coauthors " in line:
                    break

            if type_line == "person":
                #  Alternative names
                if "<author" in line:
                    name = html.unescape(line.split(">")[1].split("</author")[0])
                    names.append(name)
                #  Urls
                if "<url>" in line:
                    url = line.split(">")[1].split("</url")[0]
                    urls.append(url)
                #  End of person
                if "</person>" in line:
                    type_line = ""
                    continue

            if type_line == "conference" or "article":
                #  Author or Coauthor + possible orcid
                if "<author" in line:
                    pid = line.split('pid="')[1].split('"')[0]
                    coauthor_name = html.unescape(line.split(">")[1].split("<")[0])
                    orcid = ""
                    if "orcid" in line:
                        orcid = line.split('orcid="')[1].split('"')[0]
                    # Save new ORCID
                    if pid == dblp_id and orcid and orcid not in orcid_id:
                        orcid_id.append(orcid)
                    # If is Coauthor
                    if pid != dblp_id:
                        if pid not in coauthor:
                            coauthor[pid] = {"nombre": coauthor_name, "peso": 1}
                        else:
                            coauthor[pid]["peso"] += 1
                #  Year
                if "<year" in line:
                    year = int(line.split(">")[1].split("<")[0])
                    if year > last_publ_year:
                        last_publ_year = year
                #  End of conference
                if "</inproceedings>" in line or "</article>" in line:
                    type_line = ""
                    continue

        return {
            "names": names,
            "urls": urls,
            "n_conferences": n_conferences,
            "n_journals": n_journals,
            "orcid_id": orcid_id,
            "coauthor": coauthor,
            "last_publ_year": last_publ_year,
        }


def fetch_name_dblp(name_to_search, with_names=False):
    """
    Search name in dblp and returns candidates list. DOES NOT SAVE ANYTHING IN DATABASE.
    Input:
        name_to_search: str
    Output:
        dict: { "dblp_ids": list[str] or None, "error": str or None }
    """
    url = "https://dblp.org/search/author/api/"
    name = name_to_search.replace(" ", "%20")
    query = f"{name}&format=json"
    with httpx.Client(timeout=30) as client:
        try:
            response = client.get(
                url + "?q=" + query,
                headers={"Content-type": "application/json"},
            )
        except TimeoutException:
            raise DblpTimeOutError(f"Timeout error while accessing DBLP for name: {name_to_search}")

        except httpx.RequestError as exc:
            return {"dblp_ids": None, "error": f"Request error: {exc}"}
        except Exception as exc:
            return {"dblp_ids": None, "error": f"Unexpected error: {exc}"}
    if response.status_code != 200:
        if response.status_code in [500, 502, 503, 504]:
            raise DblpTimeOutError(f"Server error {response.status_code} while accessing DBLP for name: {name_to_search}")
        return {"dblp_ids": None, "error": f"Búsqueda invalida. Status {response.status_code}"}
    result = response.json()["result"]["hits"]
    # Invalid search
    if int(result["@total"]) > 150:
        return {"dblp_ids": None, "error": "Búsqueda invalida, más de 150 resultados."}
    # Not result but valid
    if result["@total"] == "0":
        return {"dblp_ids": None, "error": "Búsqueda invalida, sin resultados."}
    dblp_ids = [hit["info"]["url"].split("/pid/")[1] for hit in result["hit"]]
    if with_names:
        names = [hit["info"]["author"] for hit in result["hit"]]
        return {"dblp_ids": dblp_ids, "names": names, "error": None}
    return {"dblp_ids": dblp_ids, "error": None}


def infer_dblp_id(academico):
    # TODO  check this
    """
    Infer a unique DBLP ID for an academic using their name and coauthor relationships.
    Input:
    - row: dict representing a single data row
            { "model_field": "value", ...
            }
    Output:
    - suggested_value: suggested academic name (if any)
    - errors: list of error messages (if any)
    """
    query_search = academico.get_full_name_normalized()
    errors = []
    dblp_result = fetch_name_dblp(query_search)
    if dblp_result.get("error"):
        errors.append(dblp_result["error"])
    else:
        if len(dblp_result.get("dblp_ids", [])) == 1:
            dblp_id = dblp_result["dblp_ids"][0].strip('"')
            return dblp_id, None

        elif len(dblp_result.get("dblp_ids", [])) > 1:
            academicos = list(
                Academico.objects.filter(unidad__universidad=academico.unidad.universidad)
                .exclude(investigador_ondemand__isnull=True)
                .select_related("investigador_ondemand")
            )

            investigadores = [a.investigador_ondemand for a in academicos if a.investigador_ondemand]

            # Get a set of all coauthors associated with these investigadores
            coauthor_ids = set()
            investigador_ids = [inv.id for inv in investigadores]
            # Get all coauthor relationships where any investigador is involved
            coautor_qs = list(
                CoautorInvestigador.objects.filter(
                    models.Q(investigador_a_id__in=investigador_ids) | models.Q(investigador_b_id__in=investigador_ids)
                )
            )
            # Collect all related coauthor IDs (excluding the original investigadores)
            coauthor_ids = set()
            for coautor in coautor_qs:
                if coautor.investigador_a_id in investigador_ids:
                    coauthor_ids.add(coautor.investigador_b_id)
                if coautor.investigador_b_id in investigador_ids:
                    coauthor_ids.add(coautor.investigador_a_id)
            # Optionally, remove the original investigadores from the set
            coauthor_ids -= set(investigador_ids)
            # If you want the actual InvestigadorOnDemand objects:
            coauthors = list(InvestigadorOnDemand.objects.filter(id__in=coauthor_ids))
            if coauthors:
                coauthor_dblp_ids = [coauthor.dblp_id for coauthor in coauthors if coauthor.dblp_id]
                # Find intersection between the original DBLP candidates and the coauthor DBLP IDs
                intersection = set(dblp_result["dblp_ids"]).intersection(set(coauthor_dblp_ids))
                if intersection:
                    suggested_value = list(intersection)[0].strip('"')
                    return suggested_value, None
                else:
                    errors.append("No se pudo inferir un DBLP único mediante coautores")
    return None, errors


def update_investigador_dblp_data(academico, dblp_id):
    """
    Update an  investigador in db using dbpl data (n_journals,n_confenrences,last_publ_year,nombres_externos,orcid_id) and save coauthors.
    Input:
        investigador_obj: InvestigadorOnDemand object
        dblp_id: str
    Output:
        (InvestigadorOnDemand object, None) or (None,error dict )
    """
    if dblp_id:
        investigador_data = dblp_get_data(dblp_id)
        if not investigador_data:
            return None, {"error": "No se pudo obtener datos de DBLP"}
        # getting academico
        if getattr(academico, "investigador_ondemand", None):
            investigador_obj = academico.investigador_ondemand
        else:
            investigador_obj = InvestigadorOnDemand(nombre=academico.nombre, apellido=academico.apellido, academico=academico)
            investigador_obj.save()
        profile_obj, created = DblpProfile.objects.get_or_create(dblp_id=dblp_id)
        if created:
            # Create new DblpProfile
            profile_obj.dblp_n_journal = investigador_data["n_journals"]
            profile_obj.dblp_n_conference = investigador_data["n_conferences"]
            limit_year = date.today().year - 5
            profile_obj.activo = investigador_data["last_publ_year"] >= limit_year
            profile_obj.dblp_nombres_externos = investigador_data["names"]
            profile_obj.dblp_coauthors = investigador_data["coauthor"]
            if len(investigador_data["orcid_id"]) > 0:
                profile_obj.orcid_id = investigador_data["orcid_id"][0]
            profile_obj.save()
            investigador_obj.dblp_profile = profile_obj
        else:
            if InvestigadorOnDemand.objects.filter(dblp_profile=profile_obj).exclude(id=investigador_obj.id).exists():
                profile_obj.reassign_to(investigador_obj)
                # CoautorInvestigador.update_investigador_coauthors(old_investigador)
            # hanging profile or same profile
            else:
                investigador_obj.dblp_profile = profile_obj
            profile_obj.dblp_n_journal = investigador_data["n_journals"]
            profile_obj.dblp_n_conference = investigador_data["n_conferences"]
            limit_year = date.today().year - 5
            profile_obj.activo = investigador_data["last_publ_year"] >= limit_year
            profile_obj.dblp_nombres_externos = investigador_data["names"]
            profile_obj.dblp_coauthors = investigador_data["coauthor"]
            if len(investigador_data["orcid_id"]) > 0:
                profile_obj.orcid_id = investigador_data["orcid_id"][0]
            profile_obj.save()
        try:
            investigador_obj.save()
            investigador_obj.academico.dblp_last_fetched_date = timezone.now()
            CoautorInvestigador.update_investigador_coauthors(investigador_obj)
        except IntegrityError:
            return None, {"error": "Error en base de datos: Error de integridad"}
        except DataError:
            return None, {"error": "Error en base de datos: Error en algún campo"}
        except Error as error_msg_db:
            return None, {"error": f"Error en base de datos: {error_msg_db}"}
    else:
        return None, {"error": "No se pudo inferir un DBLP ID único"}
    return investigador_obj, None


def fetch_investigador_dblp_data(academico):
    """
    Update an existing investigador in db using dbpl data (n_journals,n_confenrences,last_publ_year,nombres_externos,orcid_id) and save coauthors.
    Input:
        investigador_obj: InvestigadorOnDemand object
    Output:
        (InvestigadorOnDemand object, None) or (None,error dict )
    """
    dblp_id, errors = infer_dblp_id(academico)
    if errors:
        return None, errors[0]
    return update_investigador_dblp_data(academico, dblp_id)
