import re

import requests
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import ObjectDoesNotExist
from django.db import DataError, Error, IntegrityError, transaction

from persona.models import AmbitoTrabajo, DblpProfile, InvestigadorCandidato, InvestigadorOnDemand, Keyword, KeywordInvestigador, Subarea


#  Clean html
def clean_html(html_data):
    #  Leave only body (if have >1 <html> ignore)
    if html_data.count("<html") < 2:
        if "</head>" in html_data:
            html_data = html_data.split("</head>")[1].split("</html>")[0]

    # Remove comments in html
    html_data = re.sub(r"(?=<!--)([\s\S]*?)-->", "", html_data)

    #  Replace emojis for word emoji
    emoj = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002500-\U00002bef"  # chinese char
        "\U00002702-\U000027b0"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2b55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        re.UNICODE,
    )
    html_data = re.sub(emoj, "emoji", html_data)

    return html_data


def remove_simple_tag(data):
    p = re.compile(r"<.*?>")
    return p.sub("", data)


#  Check if string has numbers
def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


#  Take a json and group their "family nodes"
def agrupador_json_recursivo(nodo):
    result = []
    results = []

    #  vals: _attributes, tags, _value, _values
    #  cada nodo con _value debe conocer sus ancestros de la forma [(tag, class,), ..]
    #  ancestro es de tipo list
    def _recorrido_recursivo(nodo, ancestro=None):
        if "_value" in nodo:
            exist = False
            for par in result:
                if par[0] == ancestro:
                    exist = True
                    par[1] = par[1] + [nodo["_value"]]
            if not exist:
                result.append([ancestro, [nodo["_value"]]])
        if "_values" in nodo:
            exist = False
            for par in results:
                if par[0] == ancestro:
                    exist = True
                    par[1] = par[1] + [nodo["_values"]]
            if not exist:
                results.append([ancestro, [nodo["_values"]]])

        # group by class -> doesnt work as planned
        classes = []
        for key, value in nodo.items():
            if key == "_attributes":
                if "class" in value:
                    classes = classes + value["class"]
        # recursion sobre cualquier tag (search first class)

        for key, value in nodo.items():
            if key == "_value" or key == "_attributes" or key == "_values":
                continue
            for child in value:
                if ancestro is None:
                    _recorrido_recursivo(child, [(key,)])
                else:
                    _recorrido_recursivo(child, ancestro + [(key,)])

        return 0

    _recorrido_recursivo(nodo)
    return result, results


#  Return (search_obj, error)
def search_name_dblp(name_to_search, store_in_db=True):
    """
    Search name in dblp and save results in InvestigadorCandidato (raw query results) and InvestigadorOnDemand(investigador data).
    Args:
        name_to_search: str
        store_in_db: bool (if False, do not store any result in db, just return them)
    Returns:
        (InvestigadorCandidato object or None, raw response or None,error dict or None)
    """
    #  Check if searched before  # TODO: Search again if stale
    searched = InvestigadorCandidato.objects.filter(buscado=name_to_search)

    if not searched:
        #  Search in dblp
        url = "https://dblp.org/search/author/api/"

        name = name_to_search.replace(" ", "%20")
        query = f"{name}&format=json"
        search_investigador = requests.get(
            url=url + "?q=" + query,
            timeout=15,
            headers={"Content-type": "application/json"},
        )

        if search_investigador.status_code != 200:
            return (None, None, {"error": "Búsqueda invalida."})

        result = search_investigador.json()["result"]["hits"]

        # Invalid search -> save search as invalid
        if int(result["@total"]) > 150:
            try:
                searched_obj = InvestigadorCandidato(
                    buscado=name_to_search,
                    valid=False,
                )
                if store_in_db:
                    searched_obj.save()
                return (
                    searched_obj,
                    None,
                    {"error": "Búsqueda invalida, más de 150 resultados."},
                )
            except IntegrityError:
                return (
                    None,
                    None,
                    {"error": "Error en base de datos: Error de intregridad"},
                )
            except DataError:
                return (
                    None,
                    None,
                    {"error": "Error en base de datos: Error en algún campo"},
                )
            except Error as error_msg_db:
                return (
                    None,
                    None,
                    {"error": f"Error en base de datos: {error_msg_db}"},
                )

        # Not result but valid -> save search as valid but no results
        if result["@total"] == "0":
            try:
                searched_obj = InvestigadorCandidato(
                    buscado=name_to_search,
                    valid=True,
                )
                if store_in_db:
                    searched_obj.save()
                return (
                    searched_obj,
                    {},
                    None,
                )
            except IntegrityError:
                return (
                    None,
                    None,
                    {"error": "Error en base de datos: Error de intregridad"},
                )
            except DataError:
                return (
                    None,
                    None,
                    {"error": "Error en base de datos: Error en algún campo"},
                )
            except Error as error_msg_db:
                return (
                    None,
                    None,
                    {"error": f"Error en base de datos: {error_msg_db}"},
                )

        # Valid search -> Save search and investigador if not exist
        dblp_ids = []
        raw_response = dict()
        for hit in result["hit"]:
            dblp_id = hit["info"]["url"].split("/pid/")[1]
            nombre = hit["info"]["author"]
            raw_response[nombre] = dblp_id
            # Check if investigador exist
            dblp_profile = DblpProfile.objects.filter(dblp_id=dblp_id)
            if not dblp_profile:
                try:
                    investigador_obj = InvestigadorOnDemand(
                        nombre=hit["info"]["author"],
                    )
                    profile_obj = DblpProfile(
                        dblp_id=dblp_id,
                        dblp_nombres_externos=[hit["info"]["author"]],
                    )
                    investigador_obj.dblp_profile = profile_obj
                    if store_in_db:
                        with transaction.atomic():
                            profile_obj.save()
                            investigador_obj.save()

                except IntegrityError:
                    return (
                        None,
                        None,
                        {"error": "Error en base de datos: Error de intregridad"},
                    )
                except DataError:
                    return (
                        None,
                        None,
                        {"error": "Error en base de datos: Error en algún campo"},
                    )
                except Error as error_msg_db:
                    return (
                        None,
                        None,
                        {"error": f"Error en base de datos: {error_msg_db}"},
                    )

        try:
            searched_obj = InvestigadorCandidato(
                buscado=name_to_search,
                valid=True,
                candidatos=dblp_ids,
            )
            if store_in_db:
                searched_obj.save()
            return (searched_obj, raw_response, None)
        except IntegrityError:
            return (
                None,
                None,
                {"error": "Error en base de datos: Error de intregridad"},
            )
        except DataError:
            return (
                None,
                None,
                {"error": "Error en base de datos: Error en algún campo"},
            )
        except Error as error_msg_db:
            return (None, None, {"error": f"Error en base de datos: {error_msg_db}"})

    else:
        searched_obj = searched.first()
        if len(searched_obj.candidatos) == 0:
            return (
                searched_obj,
                {},
                None,
            )
        else:
            raw_response = dict()
            for cand in searched_obj.candidatos:
                try:
                    dblp_profile = DblpProfile.objects.get(dblp_id=cand)

                    raw_response[f"{searched_obj.buscado}{cand}"] = cand
                except ObjectDoesNotExist:
                    pass

            return (searched_obj, raw_response, None)


def update_keywords_and_areas(investigador_obj, aminer_interests, academico_obj):
    """
    Sync: For each AMiner interest, associate/create Keyword, link to Investigador, and infer/link Subarea/AmbitoTrabajo.
    Args:
        investigador_obj: InvestigadorOnDemand instance
        aminer_interests: list of (keyword_name, peso) tuples
        academico_obj: Academico instance
    """
    if not aminer_interests:
        return
    for interest_name, peso in aminer_interests:
        # 1. Find or create Keyword (by similarity)
        keyword_qs = list(
            Keyword.objects.annotate(similarity=TrigramSimilarity("nombre", interest_name))
            .filter(similarity__gt=0.75)
            .order_by("-similarity")
        )
        if keyword_qs:
            keyword = keyword_qs[0]
        else:
            keyword = Keyword.objects.create(nombre=interest_name)

        # 2. Find or create KeywordInvestigador
        ki_qs = list(KeywordInvestigador.objects.filter(investigador=investigador_obj, keyword=keyword))
        if ki_qs:
            ki = ki_qs[0]
            if ki.peso < peso:
                ki.peso = peso
                ki.save()
        else:
            KeywordInvestigador.objects.create(investigador=investigador_obj, keyword=keyword, peso=peso)

        # 3. Infer and link Subarea/AmbitoTrabajo
        subareas = list(Subarea.objects.all())
        keyword_words = [w for w in keyword.nombre.split() if w]
        matching_subareas = [s for s in subareas if all(word.lower() in s.nombre.lower() for word in keyword_words)]
        if matching_subareas:
            areas = set(s.area for s in matching_subareas)
            if len(areas) == 1:
                area = list(areas)[0]
                otro_subarea = Subarea.objects.filter(nombre="Otro", area=area).first()
                if otro_subarea:
                    exists = AmbitoTrabajo.objects.filter(academico=academico_obj, subarea=otro_subarea).exists()
                    if not exists:
                        AmbitoTrabajo.objects.create(academico=academico_obj, subarea=otro_subarea, deleted=False, manual=False)
                for subarea in matching_subareas:
                    exists = AmbitoTrabajo.objects.filter(academico=academico_obj, subarea=subarea).exists()
                    if not exists:
                        AmbitoTrabajo.objects.create(academico=academico_obj, subarea=subarea, deleted=False, manual=False)
