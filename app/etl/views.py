import json
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import html_to_json
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import DataError, Error, IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseServerError, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from etl.utils import agrupador_json_recursivo, clean_html, has_numbers, remove_simple_tag, search_name_dblp
from persona.models import Academico, CoautorInvestigador, DblpProfile, InvestigadorCandidato, InvestigadorOnDemand
from persona.services.dblp_client import dblp_get_data
from universidad.models import Unidad, Universidad


def enviar_correo(errores, multiples_dblp, total_guardadas):
    # Configuración del correo (personalizar con tus credenciales)
    mensaje = MIMEMultipart()
    mensaje["From"] = "repositorioacademicos@gmail.com"
    mensaje["To"] = "aruz2002@gmail.com"
    mensaje["Subject"] = "Reporte de Procesamiento de Universidades"

    cuerpo = []
    cuerpo.append("=== Resumen del Procesamiento ===")

    if errores:
        cuerpo.append("\nErrores:")
        cuerpo.extend([f"- {error}" for error in errores])
    else:
        cuerpo.append("\n✅ No hubo errores")

    if multiples_dblp:
        cuerpo.append("\n🔍 Personas con múltiples DBLPs:")
        for universidad, cantidad in multiples_dblp.items():
            cuerpo.append(f"- {universidad}: {cantidad}")

    cuerpo.append(f"\n💾 Total de personas guardadas: {total_guardadas}")

    mensaje.attach(MIMEText("\n".join(cuerpo), "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("repositorioacademicos@gmail.com", "eudu mwrg dzlr ecqi")
            server.send_message(mensaje)
    except Exception as e:
        print(f"Error enviando correo: {str(e)}")


@csrf_exempt
def carga_automatica_web(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not is_ajax or request.method != "POST":
        return HttpResponseBadRequest("Invalid request method or not an AJAX request")

    try:
        # Obtener todos los IDs de universidades de la base de datos
        universidad_ids = list(Universidad.objects.values_list("id", flat=True))

        if not universidad_ids:
            return HttpResponseBadRequest("No hay universidades registradas en el sistema")

        final_result = []
        errors = []
        personas_con_varios_dblps_por_universidad = {}
        total_personas_guardadas = 0

        for universidad_id in universidad_ids:
            try:
                universidad = Universidad.objects.get(id=universidad_id)
                universidad_urls = universidad.webpage_academic

                if not universidad_urls:
                    errors.append(f"Universidad {universidad_id} ({universidad.nombre}): Sin URLs académicas")
                    continue

                data_candidate_purged = []
                url_errors = []
                personas_con_varios_dblps = 0

                # Procesamiento de URLs
                for url in universidad_urls:
                    try:
                        req = requests.get(
                            url,
                            timeout=15,
                            headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0"},
                        )
                        req.raise_for_status()

                        data = clean_html(req.text)
                        data_json = html_to_json.convert(data)
                        data_groups, _ = agrupador_json_recursivo(data_json)

                        # Filtrado de grupos
                        for group in data_groups:
                            group_candidate = list(dict.fromkeys(group[1]))
                            bad_count = sum(
                                1
                                for text in group_candidate
                                if has_numbers(text) or any(c in text for c in ["@", ":", "="]) or len(text) > 200 or len(text.split()) > 10
                            )
                            if bad_count / len(group_candidate) <= 0.75:
                                data_candidate_purged.append(group_candidate)

                    except Exception as e:
                        url_errors.append(f"Error en {url}: {str(e)}")

                if url_errors:
                    errors.append(f"Universidad {universidad_id}: Errores en URLs - {' | '.join(url_errors)}")
                    continue

                # Limpieza de textos
                data_candidate_clean = []
                for group in data_candidate_purged:
                    clean_group = []
                    for text in group:
                        text_clean = remove_simple_tag(text)
                        text_clean = text_clean.translate(str.maketrans("", "", "¡!()|{}/#"))
                        text_clean = text_clean.title().strip()
                        text_clean = text_clean.replace("Dr.", "").replace("Dra.", "").replace("Phd", "")
                        if text_clean.count(",") == 1:
                            parts = text_clean.split(",")
                            text_clean = f"{parts[1].strip()} {parts[0].strip()}"
                        clean_group.append(text_clean.strip())
                    data_candidate_clean.append(clean_group)

                # Búsqueda en DBLP
                acepted_groups = []
                for group in data_candidate_clean:
                    group_results = []
                    valid_searches = 0
                    for text in group:
                        search_text = " ".join([w for w in text.split() if len(w) > 2])

                        if len(search_text) > 200 or len(search_text.split()) == 1:
                            group_results.append(None)
                            continue

                        dblp_result = search_name_dblp(search_text)
                        if dblp_result[0] and not dblp_result[1]:  # Resultado válido sin error
                            valid_searches += 1
                            group_results.append(dblp_result[0].id)
                        else:
                            group_results.append(None)

                    # Validación final del grupo
                    is_valid = valid_searches > 0
                    if len(group) > 10 and valid_searches == 1:
                        is_valid = False
                    acepted_groups.append((is_valid, group_results))

                # Generación de resultados
                result = []
                for idx, (is_valid, group) in enumerate(acepted_groups):
                    if not is_valid:
                        continue

                    for idj, candidato_id in enumerate(group):
                        if not candidato_id:
                            continue

                        nombre_original = data_candidate_clean[idx][idj]
                        candidato = InvestigadorCandidato.objects.get(id=candidato_id)

                        # Verificar si ya existe
                        if Academico.objects.filter(unidad__universidad=universidad, nombre=nombre_original).exists():
                            continue

                        # Verificar duplicados en resultados temporales
                        if any(inv["nombre"] == nombre_original for inv in result):
                            continue

                        # Obtener candidatos DBLP
                        candidatos_dblp = []
                        for dblp_id in candidato.candidatos:
                            investigador = InvestigadorOnDemand.objects.get(dblp_id=dblp_id)
                            candidatos_dblp.append({"nombre": investigador.nombre, "dblp_id": dblp_id})

                        result.append(
                            {
                                "nombre": nombre_original,
                                "investigador_candidato_id": candidato_id,
                                "investigadores_candidatos": candidatos_dblp,
                            }
                        )

                        # Contar si tiene múltiples opciones
                        if len(candidatos_dblp) > 1:
                            personas_con_varios_dblps += 1

                # Guardar en base de datos (lógica simplificada)
                for item in result:
                    if len(item["investigadores_candidatos"]) == 1:
                        try:
                            Academico.objects.create(
                                unidad=universidad.unidad_set.first(),
                                nombre=item["nombre"],
                                dblp_id=item["investigadores_candidatos"][0]["dblp_id"],
                            )
                            total_personas_guardadas += 1
                        except Exception as e:
                            errors.append(f"Error guardando {item['nombre']}: {str(e)}")

                personas_con_varios_dblps_por_universidad[universidad.nombre] = personas_con_varios_dblps
                final_result.append(
                    {"universidad_id": universidad_id, "nombre_universidad": universidad.nombre, "personas_procesadas": len(result)}
                )

            except Exception as e:
                errors.append(f"Error crítico en universidad {universidad_id}: {str(e)}")

        # Enviar correo con resumen
        enviar_correo(errors, personas_con_varios_dblps_por_universidad, total_personas_guardadas)

        return JsonResponse(
            {
                "status": "success",
                "universidades_procesadas": len(final_result),
                "personas_guardadas": total_personas_guardadas,
                "errores": errors,
            }
        )

    except Exception as e:
        return HttpResponseServerError(f"Error general del sistema: {str(e)}")


def match_academic_web_to_dblp(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        universidad_id = json.loads(body_unicode)
        universidad_query = Universidad.objects.filter(id=universidad_id)
        if not universidad_query:
            return HttpResponseBadRequest("Invalid request")

        universidad_urls = universidad_query.first().webpage_academic

        data_candidate_all = []
        data_candidate_purged = []
        for url in universidad_urls:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
            }
            req = requests.get(url=url, timeout=15, headers=headers)
            req.encoding = "utf-8"
            data = clean_html(req.text)

            # Convert html in json
            data_json = html_to_json.convert(data)

            #  Looks like [(ancestro, [_value1, _value2],), ...]
            data_groups, _ = agrupador_json_recursivo(data_json)
            irrelevant_tags = [
                "departamento",
                "depto",
                "escuela",
                "menú",
                "carrera",
                "alternar",
                "profesores",
                "representantes",
                "vacantes",
                "malla",
                "cuerpo",
                "centros",
                "programas",
                "licenciatura",
                "campus",
                "profesor",
                "perfil",
                "asociado",
                "asistente",
                "ayudante",
                "contacto",
                "correo",
                "teléfono",
                "teléfono",
                "extensión",
                "oficina",
                "ubicación",
                "inicio",
                "ingeniería",
                "engineering",
                "engineer",
                "ingeniero",
                "ingeniera",
                "facultad",
                "universidad",
                "estudi",
                "investigación",
                "publicaciones",
                "proyectos",
                "laboratorio",
                "laboratorios",
                "dirección",
                "unidad",
                "educación",
                "postgrado",
                "posgrado",
                "postitulo",
                "diploma",
                "doctorado",
                "magíster",
                "master",
                "máster",
                "maestría",
                "pregrado",
                "grado",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "0",
                "comité",
                "centro",
                "titulo",
                "secretaría",
                "emprendimiento",
                "innovación",
                "actividades",
                "actividad",
                "noticias",
                "page",
                "movilidad",
                "internacional",
                "bibliografía",
                "bibliografia",
                "biblio",
                "investigadores",
                "investigador",
                "docentes",
                "docente",
                "vinculación",
                "quiénes somos",
                "información",
                "text",
                "tool",
                "contrast",
                "background",
                "content",
                "desarrollado",
                "profesionales",
                "read more",
                "sitio",
                "asuntos",
                "postulación",
                "portal",
                "manual",
                "herramientas",
                "campo laboral",
                "página",
                "elige",
                "guía",
                "jornada",
                "sede",
                "bolsa",
                "académico",
                "equipo",
                "estudios",
                "certificados",
                "ayuda",
                "derechos",
                "sustentable",
                "denuncias",
                "informática",
                "computación",
                "formación",
                "transparencia",
                "privacidad",
                "términos",
                "condiciones",
                "acerca",
                "contactanos",
                "contáctanos",
                "acreditación",
                "acreditacion",
                "calidad",
                "plan ",
                "curso",
            ]
            # remove texts containing tags from groups
            for group in data_groups:
                group[1] = [text for text in group[1] if not any(tag in text.lower() for tag in irrelevant_tags)]
            # remove empty groups
            data_groups = [group for group in data_groups if group[1]]

            for group in data_groups:
                group_candidate = list(dict.fromkeys(group[1]))
                data_candidate_all.append(group_candidate)
                bad = 0
                for text in group_candidate:
                    # Validate text
                    if has_numbers(text) or "@" in text or ":" in text or "=" in text:
                        bad += 1
                        continue
                    if len(text) > 200:
                        bad += 1
                        continue
                    if len(text.split(" ")) > 6:
                        bad += 1
                        continue
                if bad / len(group_candidate) <= 0.75:  # 75% tolerance
                    data_candidate_purged.append(group_candidate)

        #  Clean texts before search
        data_candidate_clean = []
        for group_text in data_candidate_purged:
            clean_text = []
            for text in group_text:
                text_clean = text
                # Remove tags like <strong>...</strong>
                text_clean = remove_simple_tag(text_clean)
                # Remove special caractars
                text_clean = text_clean.replace("¡", "")
                text_clean = text_clean.replace("!", "")
                text_clean = text_clean.replace("(", "")
                text_clean = text_clean.replace(")", "")
                text_clean = text_clean.replace("|", "")
                text_clean = text_clean.replace("{", "")
                text_clean = text_clean.replace("}", "")
                text_clean = text_clean.replace("/", "")
                text_clean = text_clean.replace("#", "")
                # Make title
                text_clean = text_clean.title()
                # Strip spaces
                text_clean = text_clean.strip()
                # Remove honorific
                text_clean = text_clean.replace("Dr.", "")
                text_clean = text_clean.replace("Dra.", "")
                text_clean = text_clean.replace("Phd", "")
                text_clean = text_clean.replace("Lic.", "")
                text_clean = text_clean.replace("Ing.", "")
                # Change position "Apellido, Nombre" -> "Nombre Apellido"
                if text_clean.count(",") == 1:
                    text_clean = " ".join((text_clean.split(",")[1]).split(" ") + (text_clean.split(",")[0]).split(" "))
                # Strip spaces
                text_clean = text_clean.strip()
                clean_text.append(text_clean)
            data_candidate_clean.append(clean_text)
        #  Search in dblp
        acepted_groups = []
        for group in data_candidate_clean:
            group_obj = []
            aceptados = 0
            for text in group:
                search_text = text
                #  Remove words with lenght 1 or 2
                search_text = " ".join([w for w in search_text.split() if len(w) > 2])

                #  Skip search impossibles or rares
                if len(search_text) > 200:
                    group_obj.append(None)
                    continue
                if len(search_text.split(" ")) == 1:
                    group_obj.append(None)
                    continue
                #  Skip problematic words (?) maybe create ddbb table for this
                if search_text in ["Data Center"]:
                    group_obj.append(None)
                    continue

                # TODO: refactor, better use  search_name_dblp(search_text,store_in_db=False) to  prevent  hanging instances
                # but needs to remove later dependency on InvestigadorCandidato for fetched data (line 391). Currently
                # etl:delete_unused_investigadores removes  hanging instances
                search_result = search_name_dblp(search_text)
                # if dblp status code != 200
                if not search_result[0]:
                    continue

                # if not error
                if not search_result[1]:
                    aceptados += 1

                group_obj.append(search_result[0].id)

            #  If only one search is valid in a big group, invalid all
            aceptado = aceptados > 0
            if len(group) > 10 and aceptados == 1:
                aceptado = False
            # if all searches are invalid, reject group
            if aceptados == 0:
                aceptado = False

            acepted_groups.append(
                (
                    aceptado,
                    group_obj,
                )
            )
        #  Generate response
        result = []
        for idx, group in enumerate(acepted_groups):
            if group[0]:
                for idj, investigador_candidato_id in enumerate(group[1]):
                    if investigador_candidato_id:
                        investigador_candidato_nombre = data_candidate_clean[idx][idj]
                        #  Get dblp id candidates
                        investigadores_candidatos_obj = InvestigadorCandidato.objects.get(id=investigador_candidato_id)
                        #  Check if already saved in db
                        academico_query = Academico.objects.filter(unidad__universidad=universidad_query.first()).filter(
                            nombre=investigador_candidato_nombre
                        )
                        if academico_query:
                            continue

                        #  Check if already included
                        exist = False
                        for candidato_ready in result:
                            if candidato_ready["nombre"] == investigador_candidato_nombre:
                                exist = True
                                break
                        if exist:
                            continue
                        investigadores_candidatos_result = []
                        # print(investigador_candidato_nombre, investigadores_candidatos_obj.candidatos)
                        for investigador_candidato_dblp_id in investigadores_candidatos_obj.candidatos:
                            investigadores_candidatos_result.append(
                                {
                                    "nombre": investigador_candidato_nombre,
                                    "dblp_id": investigador_candidato_dblp_id,
                                }
                            )
                        result.append(
                            {
                                "nombre": investigador_candidato_nombre,
                                "investigador_candidato_id": investigador_candidato_id,
                                "investigadores_candidatos": investigadores_candidatos_result,
                            }
                        )
                    else:
                        pass
        print(result)
        return JsonResponse(
            {
                # "url": url,
                # "raw_data": data_json,
                # "data": data_groups,
                # "datas": datas_groups,
                # "candidate_all": data_candidate_all,
                "candidate_clean": data_candidate_clean,
                # "acepted_groups": acepted_groups,
                "result": result,
            }
        )

    else:
        return HttpResponseBadRequest("Invalid request")


def match_name_to_dblp(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        name_to_search = json.loads(body_unicode)
        response = process_match_name_to_dblp({"name_to_search": name_to_search}, store_in_db=False)
        return JsonResponse(response)
    else:
        return HttpResponseBadRequest("Invalid request")


def match_by_coauthor(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        response = process_match_by_coauthor(data)
        return JsonResponse(response)
    else:
        return HttpResponseBadRequest("Invalid request")


def save_academico(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        data = json.loads(body_unicode)
        return process_save_academico(data)
    else:
        return HttpResponseBadRequest("Invalid request")


# Decoupled functions (without specific ajax request)
def process_match_name_to_dblp(data, store_in_db=True):
    """
    Input:
    {
      "name_to_search": "Full Name"
    }
    Output:
    {
      "dblp_cand": [
        {"dblp_id": "dblp123", "nombre": "Full Name"},
        ...
      ]
    }
    """
    name_to_search = data.get("name_to_search", "")
    buscado = " ".join([w for w in name_to_search.split() if len(w) > 2])
    candidato, raw_response, error = search_name_dblp(buscado, store_in_db=True)
    print(candidato, raw_response, error)
    if error:
        return {"error": error["error"]}
    candidatos_result = []

    for nombre, cand_dblp_id in raw_response.items():
        try:
            dblp_profile = DblpProfile.objects.get(dblp_id=cand_dblp_id)
            candidatos_result.append(
                {
                    "dblp_id": dblp_profile.dblp_id,
                    "nombre": nombre,
                }
            )
        except ObjectDoesNotExist:
            pass
    return {"dblp_cand": candidatos_result}


def process_match_by_coauthor(data):
    """
    Receives data in the form:
    {
      "universidad": <id>,
      "data": {
        "result": [
          {
            "nombre": "Full Name",
            "investigador_candidato_id": <id>,
            "investigadores_candidatos": [
              {"nombre": "Candidate Name", "dblp_id": "dblp123"},
              ...
            ]
          },
          ...
        ]
      }
    }
    Output:
    {
      "result": [
        [
          (investigador_candidato_id, dblp_id, index_in_candidates),
            ...
        ]
      ]
    }
    """
    coautor_valid = []
    universidad_id = data["universidad"]
    academicos_data = data["data"]["result"]
    universidad_obj = Universidad.objects.get(id=universidad_id)
    academico_query = Academico.objects.filter(unidad__universidad=universidad_obj)
    for academico in academico_query:
        investigador_ob = academico.investigador_ondemand
        if investigador_ob:
            coautor_valid.append(investigador_ob.dblp_id)
            coautor_investigador_query = [a.investigador_b for a in CoautorInvestigador.objects.filter(investigador_a=investigador_ob)]
            coautor_investigador_query += [a.investigador_a for a in CoautorInvestigador.objects.filter(investigador_b=investigador_ob)]
            for coautor_investigador_ob in coautor_investigador_query:
                if coautor_investigador_ob not in coautor_valid:
                    coautor_valid.append(coautor_investigador_ob.dblp_id)
    investigadores_listos = []
    investigadores_en_progreso = []
    for inv in academicos_data:
        if len(inv["investigadores_candidatos"]) == 1:
            investigadores_listos.append(inv["investigadores_candidatos"][0]["dblp_id"])
            coautor_valid.append(inv["investigadores_candidatos"][0]["dblp_id"])
        elif len(inv["investigadores_candidatos"]) > 1:
            investigadores_en_progreso.append(inv["investigador_candidato_id"])
    for investigador_bdlp_id in investigadores_listos:
        investigador_data = dblp_get_data(investigador_bdlp_id)
        investigador_obj = InvestigadorOnDemand.objects.get(dblp_profile__dblp_id=investigador_bdlp_id)
        investigador_obj.dblp_profile.dblp_n_journal = investigador_data["n_journals"]
        investigador_obj.dblp_profile.dblp_n_conference = investigador_data["n_conferences"]
        investigador_obj.dblp_profile.dblp_nombres_externos = investigador_data["names"]
        limit_year = date.today().year - 5
        investigador_obj.activo = investigador_data["last_publ_year"] >= limit_year
        if len(investigador_data["orcid_id"]) > 0:
            investigador_obj.dblp_profile.dblp_orcid_id = investigador_data["orcid_id"][0]
        investigador_obj.save()
        coautor_data_dict = investigador_data["coauthor"]
        for coautor_dblp_id, coautor_data in coautor_data_dict.items():
            investigador_coautor_obj = InvestigadorOnDemand.objects.none()

            investigador_coautor_query = InvestigadorOnDemand.objects.filter(dblp_profile__dblp_id=coautor_dblp_id)
            if not investigador_coautor_query:
                investigador_coautor_obj = InvestigadorOnDemand(
                    nombre=coautor_data["nombre"],
                    dblp_id=coautor_dblp_id,
                )
                investigador_coautor_obj.save()
            else:
                investigador_coautor_obj = investigador_coautor_query[0]
            coautor_relation_query = CoautorInvestigador.objects.filter(
                investigador_a=investigador_coautor_obj,
                investigador_b=investigador_obj,
            )
            coautor_relation_query |= CoautorInvestigador.objects.filter(
                investigador_b=investigador_coautor_obj,
                investigador_a=investigador_obj,
            )
            if not coautor_relation_query:
                coautor_relation_obj = CoautorInvestigador(
                    investigador_a=investigador_obj, investigador_b=investigador_coautor_obj, peso=coautor_data["peso"]
                )
                coautor_relation_obj.save()
            else:
                coautor_relation_obj = coautor_relation_query[0]
                coautor_relation_obj.peso = coautor_data["peso"]
                coautor_relation_obj.save()
            if investigador_coautor_obj.dblp_id not in coautor_valid:
                coautor_valid.append(investigador_coautor_obj.dblp_id)
    res = []
    repeat = True
    while repeat:
        res_loop = []
        for investigador_cand_id in investigadores_en_progreso:
            investigador_cand_obj = InvestigadorCandidato.objects.get(id=investigador_cand_id)
            investigador_probable = []
            for idx, dblp_cand in enumerate(investigador_cand_obj.candidatos):
                if dblp_cand in coautor_valid:
                    investigador_probable.append((investigador_cand_id, dblp_cand, idx))
            if investigador_probable:
                res.append(investigador_probable)
                res_loop.append(investigador_cand_id)
                if investigador_probable == 1:
                    investigador_data = dblp_get_data(investigador_probable[0][1])
                    investigador_obj = InvestigadorOnDemand.objects.get(dblp_id=investigador_probable[0][0])
                    investigador_obj.dblp_n_journal = investigador_data["n_journals"]
                    investigador_obj.dblp_n_conference = investigador_data["n_conferences"]
                    limit_year = date.today().year - 5
                    investigador_obj.activo = investigador_data["last_publ_year"] >= limit_year
                    investigador_obj.dblp_nombres_externos = investigador_data["names"]
                    if len(investigador_data["orcid_id"]) > 0:
                        investigador_obj.orcid_id = investigador_data["orcid_id"][0]
                    investigador_obj.save()
                    coautor_data_dict = investigador_data["coauthor"]
                    for coautor_dblp_id, coautor_data in coautor_data_dict.items():
                        investigador_coautor_obj = InvestigadorOnDemand.objects.none()
                        investigador_coautor_query = InvestigadorOnDemand.objects.filter(dblp_id=coautor_dblp_id)
                        if not investigador_coautor_query:
                            investigador_coautor_obj = InvestigadorOnDemand(
                                nombre=coautor_data["nombre"],
                                dblp_id=coautor_dblp_id,
                            )
                            investigador_coautor_obj.save()
                        else:
                            investigador_coautor_obj = investigador_coautor_query[0]
                        coautor_relation_query = CoautorInvestigador.objects.filter(
                            investigador_a=investigador_coautor_obj,
                            investigador_b=investigador_obj,
                        )
                        coautor_relation_query |= CoautorInvestigador.objects.filter(
                            investigador_b=investigador_coautor_obj,
                            investigador_a=investigador_obj,
                        )
                        if not coautor_relation_query:
                            coautor_relation_obj = CoautorInvestigador(
                                investigador_a=investigador_obj, investigador_b=investigador_coautor_obj, peso=coautor_data["peso"]
                            )
                            coautor_relation_obj.save()
                        else:
                            coautor_relation_obj = coautor_relation_query[0]
                            coautor_relation_obj.peso = coautor_data["peso"]
                            coautor_relation_obj.save()
                        if investigador_coautor_obj.dblp_id not in coautor_valid:
                            coautor_valid.append(investigador_coautor_obj.dblp_id)
        for r_loop in res_loop:
            investigadores_en_progreso.remove(r_loop)
        if not res_loop:
            repeat = False
    return {"resolution": res}


def process_save_academico(data):
    unidad = data["unidad_id"]
    nombre = data["nombre"].strip()
    dblp_id = data["dblp_id"]
    try:
        if unidad == "0":
            unidad_obj = Unidad.objects.filter(universidad__id=data["institucion_id"]).first()
        else:
            unidad_obj = Unidad.objects.filter(universidad__id=data["institucion_id"]).get(id=data["unidad_id"])
    except ObjectDoesNotExist:
        return JsonResponse(
            {
                "error": "Campo Unidad inconsistente",
            }
        )
    buscado = " ".join([w for w in nombre.split() if len(w) > 2])
    try:
        InvestigadorCandidato.objects.get(buscado=buscado)
    except ObjectDoesNotExist:
        return JsonResponse(
            {
                "error": "Campo Nombre inconsistente",
            }
        )

    academico_obj = Academico(
        unidad=unidad_obj,
        nombre=nombre,
        # investigador_candidato=investigador_candidato,
    )

    # Add ETL data
    investigador_ob = InvestigadorOnDemand.objects.filter(dblp_profile__dblp_id=dblp_id).first()
    if investigador_ob:
        print("EXISTS", dblp_id, investigador_ob)
    try:
        academico_obj.save()
    except IntegrityError:
        print("IntegrityError on saving Academico", academico_obj)
    except DataError:
        return JsonResponse(
            {
                "error": "Error en base de datos: Error en algún campo",
            }
        )
    except Error as error_msg_db:
        return JsonResponse(
            {
                "error": f"Error en base de datos: {error_msg_db}",
            }
        )
    return JsonResponse(
        {
            "done": "done",
        }
    )
