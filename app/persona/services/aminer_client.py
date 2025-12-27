import json

import requests
from django.db import DataError, IntegrityError
from django.utils import timezone
from django_countries import countries

from persona.models import AminerProfile, InvestigadorOnDemand, KeywordInvestigador


# Get Data from aminer
def aminer_get_data_by_name(name, afiliation_options, country):
    url = "https://searchtest.aminer.cn/aminer-search/search/person"
    data = """{
        "query": "QUERYSEARCH",
        "needDetails": true,
        "page": 0,
        "size": 1,
        "aggregations": [
            {
                "field": "authors.orgid",
                "size": 20,
                "type": "terms"
            },
            {
                "field": "authors.id",
                "size": 10,
                "type": "terms",
                "subAggregationList": [
                    {
                        "field": "year",
                        "size": 20,
                        "type": "terms",
                        "order": {
                            "field": "_key",
                            "asc": false
                        }
                    }
                ]
            }
        ],
        "filters": []
    }"""
    data = data.replace("QUERYSEARCH", name)
    aminer_response = requests.post(
        url=url,
        data=data,
        timeout=15,
        headers={"Content-Type": "application/json"},
    )
    if aminer_response.status_code == 200:
        if "data" not in aminer_response.json():
            return None, {"error": "No data in aminer response"}
        if "hitList" not in aminer_response.json()["data"]:
            return None, {"error": "No hitList in aminer response data"}
        aminer_options = aminer_response.json()["data"]["hitList"]
        #  Deambiguation process
        aminer_data = None
        for aminer_profile in aminer_options:
            if "nation" in aminer_profile:
                nation = aminer_profile["nation"].lower()
                countries_opts = [country, dict(countries)[country]]
                # check coincidece
                if any(str(opt).lower() == nation for opt in countries_opts):
                    aminer_data = aminer_profile
                    break
            if not aminer_data and "contact" in aminer_profile:
                contact = aminer_profile["contact"]
                if not aminer_data and "affiliation" in contact:
                    affiliation = contact["affiliation"].lower()
                    for aff_option in afiliation_options:
                        if aff_option.lower() in affiliation:
                            aminer_data = aminer_profile
                            break

                if not aminer_data and "bio" in contact:
                    bio = contact["bio"].lower()
                    if str(dict(countries)[country]).lower() in bio:
                        aminer_data = aminer_profile
                        break
                    for aff_option in afiliation_options:
                        if aff_option.lower() in bio:
                            aminer_data = aminer_profile
                            break

                if not aminer_data and "edu" in contact:
                    edu = contact["edu"].lower()
                    for aff_option in afiliation_options:
                        if aff_option.lower() in edu:
                            aminer_data = aminer_profile
                            break

                if not aminer_data and "work" in contact:
                    work = contact["work"].lower()
                    for aff_option in afiliation_options:
                        if aff_option.lower() in work:
                            aminer_data = aminer_profile
                            break
                if not aminer_data and "org" in contact:
                    org = contact["org"].lower()
                    for aff_option in afiliation_options:
                        if aff_option.lower() in org:
                            aminer_data = aminer_profile
                            break
        if aminer_data:
            aminer_id = aminer_data["id"]
            aminer_mail = ""
            aminer_homepage = ""
            aminer_interests = {}
            if "contact" in aminer_data:
                if "email" in aminer_data["contact"]:
                    aminer_mail = aminer_data["contact"]["email"]
                if "homepage" in aminer_data["contact"]:
                    aminer_homepage = aminer_data["contact"]["homepage"]
            if "interests" in aminer_data:
                for interest in aminer_data["interests"]:
                    aminer_interests[interest["t"]] = interest["n"]
            else:
                interests_url = "https://apiv2.aminer.cn/n?a=GetPersonInterestByID__personinterestnew.GetPersonInterestByID___"
                interests_data = """[
                    {
                        "action": "personinterestnew.GetPersonInterestByID",
                        "parameters": {
                            "person_id": "PERSONID"
                        }
                    }
                ]"""
                interests_data = interests_data.replace("PERSONID", aminer_id)
                aminer_interests_response = requests.post(
                    url=interests_url,
                    data=interests_data,
                    timeout=15,
                    headers={"Content-Type": "application/json"},
                )
                if aminer_interests_response.status_code == 200:
                    if aminer_interests_response.json()["data"][0]:
                        data_aminer_interests = aminer_interests_response.json()["data"][0]
                        if "data" in data_aminer_interests:
                            if "show_interest_info_list" in data_aminer_interests["data"]:
                                aminer_interests_data = data_aminer_interests["data"]["show_interest_info_list"]
                                for interest in aminer_interests_data:
                                    aminer_interests[interest["keyword"]] = interest["keyword_count"]
            result = {
                "aminer_id": aminer_id,
                "aminer_mail": aminer_mail,
                "aminer_homepage": aminer_homepage,
                "aminer_interests": aminer_interests,
            }
            return result, None
        else:
            return None, {"error": "Deambiguation failed"}
    else:
        return None, {"error": f"Aminer request failed with status code {aminer_response.status_code}"}


def aminer_get_data_by_id(aminer_id: str):
    """
    Fetch Amine data using the unique aminer_id instead of searching by name.
    """
    url = "https://apiv2.aminer.cn/n"
    payload = [
        {
            # "action": "aminer.PersonDetail",  # Fetch full person detail
            "parameters": {"person_id": aminer_id}
        }
    ]

    response = requests.post(
        url=url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=15,
    )

    if response.status_code != 200:
        return None

    result = response.json().get("data", [])[0]
    if not result:
        return None

    # Extract basic info
    aminer_mail = result.get("email", "")
    aminer_homepage = result.get("homepage", "")
    aminer_interests = {}
    # Extract interests
    if "interests" in result:
        for interest in result["interests"]:
            aminer_interests[interest.get("t")] = interest.get("n")
    else:
        # Fallback in case interests are stored differently
        interests_payload = [{"action": "personinterestnew.GetPersonInterestByID", "parameters": {"person_id": aminer_id}}]
        interests_response = requests.post(
            url=url,
            data=json.dumps(interests_payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if interests_response.status_code == 200:
            data_interests = interests_response.json().get("data", [])[0].get("data", {})
            for interest in data_interests.get("show_interest_info_list", []):
                aminer_interests[interest["keyword"]] = interest["keyword_count"]

    return {
        "aminer_id": aminer_id,
        "aminer_mail": aminer_mail,
        "aminer_homepage": aminer_homepage,
        "aminer_interests": aminer_interests,
    }


def fetch_investigador_aminer_data(academico):
    """
    Updates and saves InvestigadorOnDemand in db with data from aminer (aminer_id,email,webpage,keywords).
    Args:
        investigador_obj: InvestigadorOnDemand object
    Returns:
        (InvestigadorOnDemand object, None) or (None,error dict )
    """
    aminer_data, error = aminer_get_data_by_name(
        academico.get_full_name_normalized(), academico.unidad.universidad.get_alternative_names, academico.unidad.universidad.pais
    )
    if error:
        return None, error
    if aminer_data:
        # handling fetching object
        aminer_id = aminer_data["aminer_id"] if "aminer_id" in aminer_data else None
        if not aminer_id:
            return None, {"error": "No aminer_id found in fetched data"}
        else:
            response = update_investigador_aminer_data(academico, aminer_id, prefetched_data=aminer_data)
            return response
    else:
        return None, {"error": "No data returned from Aminer for given name"}


def update_investigador_aminer_data(academico, aminer_id, is_manual=False, prefetched_data=None):
    """
    Updates and saves InvestigadorOnDemand in db with data from aminer (aminer_id,email,webpage,keywords).
    Updates or creates the associated AminerProfile.
    Also updates AmbitoTrabajo for the linked Academico.
    Input:
        investigador_obj: InvestigadorOnDemand object associated to an academico.
        aminer_id: aminer id string
    Output:
        (InvestigadorOnDemand object, None) or (None,error dict )
    """

    if (
        prefetched_data
        and "aminer_id" in prefetched_data
        and "aminer_mail" in prefetched_data
        and "aminer_homepage" in prefetched_data
        and "aminer_interests" in prefetched_data
    ):
        aminer_data = prefetched_data
    else:
        aminer_data = aminer_get_data_by_id(aminer_id)
    if not aminer_data:
        return None, {"error": "No data returned from Aminer for given ID"}

    try:
        # getting investigoador  from academico
        if getattr(academico, "investigador_ondemand", None):
            investigador_obj = academico.investigador_ondemand
        else:
            investigador_obj = InvestigadorOnDemand(nombre=academico.nombre, apellido=academico.apellido, academico=academico)
            investigador_obj.save()
        # Handling AminerProfile
        aminer_profile, created = AminerProfile.objects.get_or_create(aminer_id=aminer_data["aminer_id"])
        if created:
            investigador_obj.aminer_profile = aminer_profile
            if aminer_data["aminer_mail"]:
                aminer_profile.aminer_email = aminer_data["aminer_mail"]
            if aminer_data["aminer_homepage"]:
                aminer_profile.aminer_webpage = aminer_data["aminer_homepage"]
            if aminer_data["aminer_interests"]:
                assert isinstance(aminer_data["aminer_interests"], dict)
                aminer_profile.aminer_interests = aminer_data["aminer_interests"]
            aminer_profile.save()
            investigador_obj.save()
            KeywordInvestigador.update_investigador_keywords(investigador_obj)
        else:
            if aminer_data["aminer_mail"]:
                aminer_profile.aminer_email = aminer_data["aminer_mail"]
            if aminer_data["aminer_homepage"]:
                aminer_profile.aminer_webpage = aminer_data["aminer_homepage"]
            if aminer_data["aminer_interests"]:
                assert isinstance(aminer_data["aminer_interests"], dict)
                aminer_profile.aminer_interests = aminer_data["aminer_interests"]
            aminer_profile.save()
            # edge case: existing profile assigned  to another investigador
            if InvestigadorOnDemand.objects.filter(aminer_profile=aminer_profile).exclude(id=investigador_obj.id).exists():
                aminer_profile.reassign_to(investigador_obj)
            # reassign profile to current investigador
            else:
                investigador_obj.aminer_profile = aminer_profile
                investigador_obj.save()
                KeywordInvestigador.update_investigador_keywords(investigador_obj)

        investigador_obj.academico.aminer_last_fetched_date = timezone.now()
        investigador_obj.academico.save()
        return investigador_obj, None

    except IntegrityError as e:
        return None, {"error": f"Integrity error: {str(e)}"}
    except DataError as e:
        return None, {"error": f"Data error: {str(e)}"}
    except Exception as e:
        return None, {"error": f"Unexpected error: {str(e)}"}
