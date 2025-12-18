import json

from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.db.models import Count, Q, Value
from django.db.models.functions import Coalesce, Concat, Greatest
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django_countries import countries as d_countries

from front.serializers import build_serialized_data
from grados.forms import SanitizeAcademicoForm, SanitizeGradoForm, SanitizeInstitucionForm
from grados.models import GradoInstancia, GradoTipo
from persona.models import (
    Academico,
    AcademicoInvitacion,
    AmbitoTrabajo,
    Area,
    CoautorInvestigador,
    Keyword,
    KeywordInvestigador,
    Subarea,
)
from universidad.models import (
    SecretarioInstitucion,
    SecretarioInstitucionInvitacion,
    Unidad,
    Universidad,
)
from users.models import User


def index(request):
    count_universidad = Universidad.objects.all().count()
    count_academicos = Academico.objects.all().count()
    count_grados = GradoInstancia.objects.all().count()

    # Countries (show only countries with universities)
    countries_query = Universidad.objects.order_by("pais").exclude(pais="0").values("pais").distinct()
    countries = []
    for country in countries_query:
        countries.append(
            {
                "code": country["pais"],
                "name": dict(d_countries)[country["pais"]],
            }
        )

    # Areas-Subareas
    areas_context = {"areas": []}
    areas_objs = Area.objects.all()
    for area_obj in areas_objs:
        areas_context["areas"].append(
            {
                "nombre": area_obj.nombre,
                "id": area_obj.id,
                "subareas": [],
            }
        )
        subarea_valid = [
            a["subarea"] for a in AmbitoTrabajo.objects.filter(subarea__area=area_obj).values("subarea").exclude(deleted=True).distinct()
        ]
        subareas_objs = Subarea.objects.filter(id__in=subarea_valid).exclude(nombre="Otro")
        for subarea_obj in subareas_objs:
            areas_context["areas"][-1]["subareas"].append(
                {
                    "nombre": subarea_obj.nombre,
                    "id": subarea_obj.id,
                }
            )

    context = {
        "count_universidad": count_universidad,
        "count_academicos": count_academicos,
        "count_grados": count_grados,
        "countries": countries,
        "areas_subareas": areas_context,
    }
    return render(request, "front/index.html", context)


def buscar(request):
    # retrieving  context data
    # Countries (show only countries with universities)
    objects_per_page = 5
    countries_query = Universidad.objects.order_by("pais").exclude(pais="0").values("pais").distinct()
    countries = []
    for country in countries_query:
        countries.append(
            {
                "code": country["pais"],
                "name": dict(d_countries)[country["pais"]],
            }
        )

    # Areas-Subareas
    areas_context = {"areas": []}
    areas_objs = Area.objects.all()
    for area_obj in areas_objs:
        areas_context["areas"].append(
            {
                "nombre": area_obj.nombre_es,
                "id": area_obj.id,
                "subareas": [],
            }
        )
        subareas_objs = Subarea.objects.filter(area=area_obj)
        for subarea_obj in subareas_objs:
            areas_context["areas"][-1]["subareas"].append(
                {
                    "nombre": subarea_obj.nombre_es,
                    "id": subarea_obj.id,
                }
            )
    # grados
    grados_context = [choice for choice in GradoTipo.choices if choice[0] != GradoTipo.UNKNOWN]  # excluding unknown
    # Query
    query_original = request.GET.get("q", "")
    query = request.GET.get("q", "").lower()
    # parse query
    query_items = [item.strip() for item in query.split(";") if item.strip()][:3]  # max 3 items
    filter_pais = request.GET.get("fp", "")
    filter_area = int(request.GET.get("fa", "0"))
    filter_subarea = int(request.GET.get("fs", "0"))
    filter_grado = request.GET.get("fg", "")
    uni_page_num = request.GET.get("pu", "1")
    acad_page_num = request.GET.get("pa", "1")
    grado_page_num = request.GET.get("pg", "1")
    current_section = request.GET.get("section", "academicos")  # academicos, universidades, grados

    # Universidades
    universidades_objs = Universidad.objects.all()
    universidades_acc = Universidad.objects.none()
    if query_items:
        for query_item in query_items:
            # exact match by sigla
            universidades_items = Universidad.objects.filter(Q(sigla__iexact=query_item))
            # contain match  by name
            if not len(universidades_items):
                universidades_items = Universidad.objects.filter(Q(nombre__icontains=query_item))

            universidades_acc = universidades_acc | universidades_items

        universidades_objs = universidades_acc.distinct()
    # filtering
    if filter_pais:
        universidades_objs = universidades_objs.filter(pais=filter_pais)

    universidades_objs = universidades_objs.order_by_priority(query=query_items)
    # pagination
    uni_paginator = Paginator(universidades_objs, objects_per_page)
    try:
        universidades_objs = uni_paginator.page(uni_page_num)
    except Exception:
        universidades_objs = uni_paginator.page(1)

    # Academicos
    academicos_group = []  # [Academico, Investigador, [subareas], [keywords], [areas]]
    academicos = Academico.objects.all()
    academicos_empty_qs = Academico.objects.none()
    keywords = Keyword.objects.none()
    names_query = []
    if query_items:
        for item in query_items:
            keywords |= Keyword.objects.filter(nombre__iexact=item)
        for query_item in query_items:
            academicos_item = academicos.annotate(
                full_name=Concat(
                    Coalesce("nombre", Value("")),
                    Value(" "),
                    Coalesce("apellido", Value("")),
                )
            ).filter(full_name__icontains=query_item)

            if not len(academicos_item):
                academicos_item = academicos.annotate(
                    similarity=TrigramSimilarity(
                        Concat(
                            Coalesce("nombre", Value("")),
                            Value(" "),
                            Coalesce("apellido", Value("")),
                        ),
                        query_item,
                    ),
                ).filter(similarity__gt=0.5)
            if academicos_item.exists():
                names_query.append(query_item)
            if keywords.exists():
                academicos_keywords = academicos.filter(investigador_ondemand__keywordinvestigador__keyword__in=keywords)
                academicos_item = academicos_item | academicos_keywords
            academicos_empty_qs = academicos_empty_qs | academicos_item

        academicos = academicos_empty_qs.distinct()
    # filtering

    if filter_area:
        academicos_ambitos_ids = AmbitoTrabajo.objects.filter(subarea__area__id=filter_area).values_list("academico", flat=True).distinct()
        academicos = academicos.filter(id__in=academicos_ambitos_ids)
    if filter_subarea:
        academicos_ambitos_ids = AmbitoTrabajo.objects.filter(subarea__id=filter_subarea).values_list("academico", flat=True).distinct()
        academicos = academicos.filter(id__in=academicos_ambitos_ids)

    if filter_pais:
        academicos = academicos.filter(unidad__universidad__pais=filter_pais)
    # sorting
    academicos = academicos.order_by_priority(names_query=names_query, keywords=keywords)
    # pagination
    acad_paginator = Paginator(academicos, objects_per_page)
    try:
        academicos = acad_paginator.page(acad_page_num)
    except Exception:
        academicos = acad_paginator.page(1)

    for academico_obj in academicos.object_list:
        investigador_q = academico_obj.investigador_ondemand
        if investigador_q:
            academicos_group.append(
                [
                    academico_obj,
                    investigador_q,
                    [],
                    [],
                    [],
                ]
            )
        else:
            academicos_group.append(
                [
                    academico_obj,
                    None,
                    [],
                    [],
                    [],
                ]
            )

    #  Get the rest of areas for academico
    for academico_group in academicos_group:
        # [Academico, Investigador, [subareas], [keywords], [areas]]
        academico_ambitos = academico_group[0].ambitotrabajo_set.all()
        academico_group[2] = list(academico_ambitos.exclude(deleted=True).select_related("subarea").order_by("-peso")[:3])
        if academico_group[1] and getattr(academico_group[1], "aminer_profile"):
            keywords = [(keyword, peso) for keyword, peso in academico_group[1].aminer_profile.aminer_interests.items()]
            keywords.sort(key=lambda x: x[1], reverse=True)
            keywords = [x[0] for x in keywords][:20]
            academico_group[3] = keywords

        subarea_ids = academico_ambitos.values_list("subarea", flat=True)
        academico_group[4] = [area for area in Area.objects.filter(subarea__in=subarea_ids).distinct()]
    academicos_group = {"objects": academicos_group, "paginated": academicos}
    # Grados
    grados_objs = GradoInstancia.objects.all()
    grados_acc = GradoInstancia.objects.none()
    if query_items:
        for query_item in query_items:
            grados_item = (
                GradoInstancia.objects.filter(unidad__is_deleted=False)
                .annotate(
                    sim_nombre_en=TrigramSimilarity("nombre_en", query_item),
                    sim_nombre_es=TrigramSimilarity("nombre_es", query_item),
                )
                .annotate(similarity=Greatest("sim_nombre_en", "sim_nombre_es"))
                .filter(similarity__gt=0.15)
            )
            # filtering
            grados_acc = grados_acc | grados_item
        grados_objs = grados_acc.distinct()
    # filtering
    if filter_pais:
        grados_objs = grados_objs.filter(unidad__universidad__pais=filter_pais)
    if filter_grado:
        grados_objs = grados_objs.filter(tipo=filter_grado)
    # sorting
    grados_objs = grados_objs.order_by_priority(query=query_items)
    # PAGINATION
    grado_paginator = Paginator(grados_objs, objects_per_page)
    try:
        grados_objs = grado_paginator.page(grado_page_num)
    except Exception:
        grados_objs = grado_paginator.page(1)

    context = {
        "query": query_original,
        "fp": filter_pais,
        "fa": filter_area,
        "fs": filter_subarea,
        "fg": filter_grado,
        "current_section": current_section,
        "academicos_group": academicos_group,
        "academicos_paginator": acad_paginator,
        "universidades": universidades_objs,
        "universidades_paginator": uni_paginator,
        "programas": grados_objs,
        "grados_paginator": grado_paginator,
        "header_text": "Búsqueda",
        "countries": countries,
        "areas": areas_objs,
        "areas_subareas": areas_context,
        "grados": grados_context,
    }
    return render(request, "front/buscar.html", context)


def instituciones(request):
    instituciones_per_page = 8
    # Get Secretario Institucion if user
    instituciones_secretario_list = []
    if request.user.is_authenticated:
        instituciones_secretario_list = [si.institucion for si in SecretarioInstitucion.objects.filter(user=request.user).all()]
        for inst in instituciones_secretario_list:
            inst.editable = True
    # Omit soft-deleted institutions
    institutions_qs = Universidad.objects.filter(is_deleted=False)
    # Country filter
    country_filter = request.GET.get("c", "")
    country_filter_name = ""
    if country_filter:
        instituciones_list = (
            institutions_qs.filter(pais=country_filter).exclude(id__in=[i.id for i in instituciones_secretario_list]).order_by("id").all()
        )
        country_filter_name = dict(d_countries)[country_filter]
    else:
        instituciones_list = institutions_qs.exclude(id__in=[i.id for i in instituciones_secretario_list]).order_by("id").all()

    # Page
    len_inst = len(instituciones_list) + len(instituciones_secretario_list)
    page = int(request.GET.get("p", "1"))
    pages = int(len_inst / instituciones_per_page) + (len_inst % instituciones_per_page > 0)
    if page < 1:
        page = 1
    if page > pages:
        page = pages

    # Countries (show only countries with universities)
    countries_query = Universidad.objects.order_by("pais").exclude(pais="0").values("pais").distinct()
    countries = []
    for country in countries_query:
        countries.append(
            {
                "code": country["pais"],
                "name": dict(d_countries)[country["pais"]],
            }
        )

    instituciones_list_show = list(instituciones_secretario_list) + list(instituciones_list)
    context = {
        "instituciones_list": instituciones_list_show[
            (page - 1) * instituciones_per_page : (page - 1) * instituciones_per_page + instituciones_per_page
        ],
        "items_per_page": instituciones_per_page,
        "pages": range(1, pages + 1),
        "current_page": page,
        "country_filter": country_filter,
        "country_filter_name": country_filter_name,
        "last_page": pages,
        "rest": range(instituciones_per_page - len_inst % instituciones_per_page),
        "header_text": "Instituciones",
        "countries": countries,
    }
    return render(request, "front/instituciones.html", context)


def academico(request, id_academico):
    anonimo = bool(request.GET.get("a", ""))
    academico_ob = get_object_or_404(Academico, id=id_academico)

    # Check if user can edit
    editable = request.user.is_staff or academico_ob.user == request.user
    if not editable and request.user.is_authenticated:
        sec_insts_query = SecretarioInstitucion.objects.filter(
            user=request.user,
            institucion=academico_ob.unidad.universidad,
        ).all()
        if sec_insts_query:
            editable = True

    investigador_ob = None
    keywords_investigador_obs = []

    if academico_ob.investigador_ondemand:
        investigador_ob = academico_ob.investigador_ondemand
        keywords_investigador_obs = KeywordInvestigador.objects.filter(investigador=investigador_ob).order_by("-peso")

    # Email (anti-scrapper)
    email = None
    if investigador_ob and investigador_ob.aminer_email:
        email = (
            investigador_ob.aminer_email.split("@")[0],
            investigador_ob.aminer_email.split("@")[1],
        )

    # Areas - Subareas
    subareas_ambitos = (
        academico_ob.ambitotrabajo_set.exclude(subarea__nombre__in=["Other", "Otro"]).exclude(deleted=True).order_by("peso")[:20]
    )
    subarea_ids = AmbitoTrabajo.objects.filter(academico=academico_ob).values_list("subarea", flat=True)

    areas = Area.objects.filter(subarea__in=subarea_ids).distinct()

    if investigador_ob and getattr(investigador_ob, "aminer_profile"):
        keywords = [(keyword, peso) for keyword, peso in investigador_ob.aminer_profile.aminer_interests.items()]
        keywords.sort(key=lambda x: x[1], reverse=True)
        keywords = [x[0] for x in keywords][:20]
    else:
        keywords = []

    # Coautores
    coautores = []  # [[investigador, peso, academico], ...]
    coautores_dblp_id = set()
    coautores_peso_total = 0

    if investigador_ob:
        coautores_qs = CoautorInvestigador.objects.filter(investigador_a=investigador_ob).select_related(
            "investigador_b"
        ) | CoautorInvestigador.objects.filter(investigador_b=investigador_ob).select_related("investigador_a")

        coautores_investigadores = {
            coautor.investigador_b: coautor.peso for coautor in coautores_qs if coautor.investigador_b != investigador_ob
        }
        coautores_investigadores.update(
            {coautor.investigador_a: coautor.peso for coautor in coautores_qs if coautor.investigador_a != investigador_ob}
        )

        # Fetch all related Academico objects in a single query
        academico_coautores = Academico.objects.filter(investigador_ondemand__in=coautores_investigadores.keys()).select_related(
            "investigador_ondemand"
        )

        # Map coauthors to their Academico objects
        academico_map = {a.investigador_ondemand: a for a in academico_coautores}

        # Build the coautores list
        for investigador, peso in coautores_investigadores.items():
            coautores_peso_total += peso
            coautores_dblp_id.add(investigador.dblp_id)
            coautores.append([investigador, peso, academico_map.get(investigador)])

        # Sort coauthors by weight
        coautores.sort(key=lambda a: a[1], reverse=True)

    # Coautores distancia 2
    coautores_distance_2 = {}  # dblp_id: {nombre, peso_ponderado, peso, academico}
    coautores_ids = [coautor[0].id for coautor in coautores if coautor[2]]  # only for academicos coautores
    coautores_distance_2_qs = (
        CoautorInvestigador.objects.filter(Q(investigador_a_id__in=coautores_ids) | Q(investigador_b_id__in=coautores_ids))
        .select_related("investigador_a", "investigador_b")
        .distinct()
        .order_by("-peso")[:400]
        # limit to 400  for prevent performance issues
    )

    # adding investigators at distance 2, filters to avoid direct coauthors and self
    investigadores_d2 = set()
    for coautor_d2 in coautores_distance_2_qs:
        if coautor_d2.investigador_a != investigador_ob and coautor_d2.investigador_b != investigador_ob:
            if coautor_d2.investigador_a_id not in coautores_ids:
                investigadores_d2.add(coautor_d2.investigador_a)
            if coautor_d2.investigador_b_id not in coautores_ids:
                investigadores_d2.add(coautor_d2.investigador_b)

    academico_d2_map = {
        academico.investigador_ondemand: academico for academico in Academico.objects.filter(investigador_ondemand__in=investigadores_d2)
    }
    # building coauthors at distance 2
    for coautor_d2 in coautores_distance_2_qs:
        investigador_d2 = coautor_d2.investigador_a if coautor_d2.investigador_a_id not in coautores_ids else coautor_d2.investigador_b
        # Skip if the investigator is the main one or a direct coauthor
        if investigador_d2.dblp_id == investigador_ob.dblp_id or investigador_d2.dblp_id in coautores_dblp_id:
            continue
        # Add or update the coauthor at distance 2
        if investigador_d2.dblp_id not in coautores_distance_2:
            coautores_distance_2[investigador_d2.dblp_id] = {
                "nombre": investigador_d2.nombre,
                "peso_ponderado": coautor_d2.peso,
                "peso": coautor_d2.peso,
                "academico": academico_d2_map.get(investigador_d2),
            }
            if investigador_d2.orcid_id:
                coautores_distance_2[investigador_d2.dblp_id]["orcid_id"] = investigador_d2.orcid_id
    # # sorting
    # coautores_distance_2 = dict(sorted(coautores_distance_2.items(), key=lambda item: item[1]["peso_ponderado"], reverse=True))
    context = {
        "academico": academico_ob,
        "investigador": investigador_ob,
        "email": email,
        "areas": areas,
        "subareas_ambitos": subareas_ambitos,
        "keywords": keywords,
        "coautores": coautores,
        "coautores_d2": coautores_distance_2,
        "keywords_investigador": keywords_investigador_obs[:20],
        "anonimo": anonimo,
        "editable": editable,
        "header_text": "Académico",
    }
    return render(request, "front/academico.html", context)


def academico_edit(request, id_academico):
    academico_ob = get_object_or_404(Academico, id=id_academico)
    has_secretario_permission = SecretarioInstitucion.objects.filter(
        user=request.user,
        institucion=academico_ob.unidad.universidad,
    ).exists()
    has_academico_permission = academico_ob.user == request.user

    if not request.user.is_superuser and not has_secretario_permission and not has_academico_permission:
        return redirect("front:academico", id_academico=id_academico)

    investigador_ob = academico_ob.investigador_ondemand
    # Areas
    areas_context = {"areas": []}
    areas_objs = Area.objects.all()
    for area_obj in areas_objs:
        areas_context["areas"].append(
            {
                "nombre": area_obj.nombre,
                "nombre_es": area_obj.nombre_es,
                "id": area_obj.id,
                "subareas": [],
            }
        )

        subareas_except_other = Subarea.objects.filter(area=area_obj).exclude(nombre__in=["Other", "Otro"])
        other_subareas = Subarea.objects.filter(area=area_obj, nombre__in=["Other", "Otro"])
        subareas_objs = list(subareas_except_other) + list(other_subareas)
        for subarea_obj in subareas_objs:
            areas_context["areas"][-1]["subareas"].append(
                {
                    "nombre": subarea_obj.nombre,
                    "nombre_es": subarea_obj.nombre_es,
                    "id": subarea_obj.id,
                }
            )

    ambitos_subareas = ";".join(
        [
            str(a.subarea.id) + ":" + str(a.subarea.area.id)
            for a in AmbitoTrabajo.objects.filter(academico=academico_ob)
            # .exclude(subarea__nombre="Otro")
            .exclude(deleted=True)
        ]
    )
    ambitos_areas = ";".join(
        [
            str(a.subarea.area.id)
            for a in AmbitoTrabajo.objects.filter(academico=academico_ob)
            # .filter(subarea__nombre="Otro")
            .exclude(deleted=True)
        ]
    )
    # openalex suggestions
    openalex_subareas_ids = []
    openalex_ambitos_suggestion = {}
    if investigador_ob and getattr(investigador_ob, "openalex_profile"):
        openalex_subareas_suggestion = investigador_ob.openalex_profile.openalex_topics
        openalex_subareas_ids = Subarea.objects.filter(nombre_en__in=openalex_subareas_suggestion.keys())
        # output areaid:[subareas id]
        for subarea in openalex_subareas_ids:
            if subarea.area.id not in openalex_ambitos_suggestion:
                openalex_ambitos_suggestion[subarea.area.id] = []
            openalex_ambitos_suggestion[subarea.area.id].append(subarea.id)

    # Unidades context
    # {pais_code : {country_label: "", unidades: {id: "uni - unidad"}}}
    unidades_qs = Unidad.objects.filter(is_deleted=False).select_related("universidad").order_by("universidad__pais", "nombre")
    unidades_context = {}
    dict_countries = dict(d_countries)
    for unidad in unidades_qs:
        # d_countries
        pais_code = str(unidad.universidad.pais)
        if pais_code not in unidades_context:
            unidades_context[pais_code] = {}
        if "unidades" not in unidades_context[pais_code]:
            unidades_context[pais_code]["unidades"] = {}
        unidades_context[pais_code]["unidades"][unidad.id] = f"{unidad.universidad.nombre} - {unidad.nombre}"
        unidades_context[pais_code]["country_label"] = dict_countries.get(pais_code, pais_code)
    # Sort the "unidades" dictionary for each country by string representation
    for pais_code in unidades_context:
        unidades_context[pais_code]["unidades"] = [
            {"id": unidad_id, "label": label}
            for unidad_id, label in sorted(unidades_context[pais_code]["unidades"].items(), key=lambda x: x[1])
        ]

    context = {
        "academico": academico_ob,
        "investigador": investigador_ob,
        "unidad": academico_ob.unidad,
        "ambitos_subareas": ambitos_subareas,
        "openalex_ambitos_suggestion": openalex_ambitos_suggestion,
        "ambitos_areas": ambitos_areas,
        "areas_all": areas_context,
        "unidades_context": unidades_context,
        "header_text": "Editar Academico",
    }
    return render(request, "front/academico_edit.html", context)


def institucion(request, id_institucion):
    # Get Secretario Institucion if user
    editable = request.user.is_staff
    if request.user.is_authenticated:
        insts_query = SecretarioInstitucion.objects.filter(
            user=request.user,
            institucion__id=id_institucion,
        ).all()
        if insts_query:
            editable = True

    universidad_ob = get_object_or_404(Universidad, id=id_institucion)
    anonimo = bool(request.GET.get("a", ""))
    unidades = Unidad.objects.filter(universidad__id=id_institucion).filter(is_deleted=False).all()
    # sort unidades, default  ones last
    unidades = sorted(unidades, key=lambda u: u.is_default)

    academicos = []
    for unidad in unidades:
        academicos_unidad = Academico.objects.filter(unidad=unidad).all().order_by_priority()
        for academico_ob in academicos_unidad:
            if academico_ob.investigador_ondemand:
                investigador = academico_ob.investigador_ondemand
                # Change academico value but dont save in database
                if investigador.orcid_id:
                    academico_ob.orcid_id = investigador.orcid_id
                academico_ob.dblp_n_journal = investigador.dblp_n_journal
                academico_ob.dblp_n_conference = investigador.dblp_n_conference
            academicos.append(academico_ob)

    # Add academicos with unidad=None but universidad matches
    academicos_sin_unidad = Academico.objects.filter(
        unidad__isnull=True,
        # universidad=universidad_ob
    ).all()

    for academico_ob in academicos_sin_unidad:
        academicos.append(academico_ob)
    # Programas
    programas = GradoInstancia.objects.filter(unidad__universidad=universidad_ob).all().order_by_priority()
    context = {
        "universidad": universidad_ob,
        "unidades": unidades,
        "academicos": academicos,
        "grados": programas,
        "tipo_choices": GradoInstancia._meta.get_field("tipo").choices,
        "anonimo": anonimo,
        "editable": editable,
        "header_text": "Institución",
    }
    return render(request, "front/institucion.html", context)


def universidad_link_new(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        data_request = json.loads(body_unicode)
        universidad_id = data_request["universidad"]
        link_new = data_request["link"]

        universidad_obj = Universidad.objects.get(id=universidad_id)
        if link_new not in universidad_obj.webpage_academic:
            universidad_obj.webpage_academic.append(link_new)
            universidad_obj.save()
            return JsonResponse(
                {
                    "result": "done",
                }
            )
        else:
            return HttpResponseBadRequest("Invalid request")
    else:
        return HttpResponseBadRequest("Invalid request")


def universidad_link_delete(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        data_request = json.loads(body_unicode)
        universidad_id = data_request["universidad"]
        link_delete = str(data_request["link"])

        universidad_obj = Universidad.objects.get(id=universidad_id)
        if link_delete in universidad_obj.webpage_academic:
            universidad_obj.webpage_academic.remove(link_delete)
            universidad_obj.save()

            return JsonResponse(
                {
                    "links_count": len(universidad_obj.webpage_academic),
                }
            )
        else:
            return HttpResponseBadRequest("Invalid request")
    else:
        return HttpResponseBadRequest("Invalid request")


def carga_masiva(request, id_universidad):
    universidad_ob = get_object_or_404(Universidad, id=id_universidad)
    unidades_objs = Unidad.objects.filter(universidad__id=id_universidad).filter(is_deleted=False).all()
    academicos_objs = []
    for unidad in unidades_objs:
        academicos_unidad = Academico.objects.filter(unidad=unidad).all()
        for academico_obj in academicos_unidad:
            academicos_objs.append(academico_obj)
    context = {
        "universidad": universidad_ob,
        "unidades": unidades_objs,
        "academicos": academicos_objs,
        "header_text": "Carga Masiva",
    }
    return render(request, "front/carga_masiva.html", context)


def usuarios(request):
    if not request.user.is_superuser:
        return redirect("front:index")

    users = User.objects.all()
    for user in users:
        user.instituciones = [si.institucion for si in SecretarioInstitucion.objects.filter(user=user).all()]
    instituciones_query = Universidad.objects.order_by("nombre").all()
    context = {
        "users": users,
        "instituciones": instituciones_query,
    }
    return render(request, "front/usuarios.html", context)


def usuario_invitacion(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        institucion_id = json.loads(body_unicode)
        institucion_obj = Universidad.objects.filter(id=institucion_id).first()
        expiration = timezone.now() + timezone.timedelta(days=1)
        new_invitacion = SecretarioInstitucionInvitacion(institucion=institucion_obj, expiration=expiration)
        new_invitacion.save()
        return JsonResponse(
            {
                "code": new_invitacion.code,
                "url": reverse(
                    "users:registro",
                    kwargs={"invitation_code": new_invitacion.code},
                ),
            }
        )
    else:
        return HttpResponseBadRequest("Invalid request")


def usuario_delete(request):
    user_mail = request.GET.get("user", "")
    if not user_mail:
        return redirect("front:index")
    else:
        user_obj = User.objects.filter(email=user_mail).first()
        user_obj.delete()
        return redirect("front:usuarios")


def areas(request):
    if not request.user.is_superuser:
        return redirect("front:index")

    areas_objs = Area.objects.all()
    for area_obj in areas_objs:
        area_obj.sub_areas = Subarea.objects.filter(area=area_obj).exclude(nombre__in=["Other", "Otro"]).all()
    context = {
        "areas": areas_objs,
    }

    return render(request, "front/areas.html", context)


def api(request):
    return render(request, "front/api.html")


def usuario_invitacion_academico(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax and request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        academico_id = json.loads(body_unicode)
        academico_obj = Academico.objects.filter(id=academico_id).first()
        expiration = timezone.now() + timezone.timedelta(days=1)
        new_invitacion = AcademicoInvitacion(academico=academico_obj, expiration=expiration)
        new_invitacion.save()
        return JsonResponse(
            {
                "code": new_invitacion.code,
                "url": reverse(
                    "users:registro_academico",
                    kwargs={"invitation_code": new_invitacion.code},
                ),
            }
        )
    else:
        return HttpResponseBadRequest("Invalid request")


def carga_automatica(request):
    # Get required and optional fields
    if not request.user.is_superuser:
        return render(request, "front/index.html", status=403)
    if request.method != "GET":
        return render(request, "front/index.html", status=400)

    context = {
        "modelFields": {
            "grados": {
                "required": SanitizeGradoForm.get_required_fields(),
                "optional": SanitizeGradoForm.get_optional_fields(),
                "tags": SanitizeGradoForm.get_field_tags(),
                "field_descriptions": SanitizeGradoForm.get_field_descriptions(),
            },
            "academicos": {
                "required": SanitizeAcademicoForm.get_required_fields(),
                "optional": SanitizeAcademicoForm.get_optional_fields(),
                "tags": SanitizeAcademicoForm.get_field_tags(),
                "field_descriptions": SanitizeAcademicoForm.get_field_descriptions(),
            },
            "instituciones": {
                "required": SanitizeInstitucionForm.get_required_fields(),
                "optional": SanitizeInstitucionForm.get_optional_fields(),
                "tags": SanitizeInstitucionForm.get_field_tags(),
                "field_descriptions": SanitizeInstitucionForm.get_field_descriptions(),
            },
        }
    }

    return render(request, "front/carga_automatica.html", context)


def grado(request, id_grado):
    grado_obj = get_object_or_404(GradoInstancia, id=id_grado)
    unidad = grado_obj.unidad
    universidad = unidad.universidad if unidad else None
    verifiaction_error = grado_obj.get_verification_error()
    # Check if user can edit
    editable = True
    if request.user.is_authenticated:
        has_secretario_permission = SecretarioInstitucion.objects.filter(
            user=request.user,
            institucion=grado_obj.unidad.universidad,
        ).exists()
    else:
        has_secretario_permission = False

    if not request.user.is_superuser and not has_secretario_permission:
        editable = False
    context = {
        "grado": grado_obj,
        "unidad": unidad,
        "universidad": universidad,
        "editable": editable,
        "header_text": "Programa",
        "verification_error": verifiaction_error,
    }
    return render(request, "front/grado.html", context)


def indicadores(request):
    context = {
        "model_choices": [
            {"value": "academicos", "label": "Académicos"},
            {"value": "universidades", "label": "Universidades"},
            {"value": "grados", "label": "Programas"},
        ],
        "group_by_choices": {
            "academicos": [
                {"value": "pais", "label": "País"},
                {"value": "universidad", "label": "Universidad"},
            ],
            "universidades": [
                {"value": "pais", "label": "País"},
            ],
            "grados": [
                {"value": "pais", "label": "País"},
                {"value": "universidad", "label": "Universidad"},
                {"value": "tipo", "label": "Tipo de Grado"},
            ],
        },
        "filter_by_choices": {
            "academicos": [
                {"value": "pais", "label": "País"},
                {"value": "universidad", "label": "Universidad"},
            ],
            "universidades": [
                {"value": "pais", "label": "País"},
            ],
            "grados": [
                {"value": "pais", "label": "País"},
                {"value": "universidad", "label": "Universidad"},
                {"value": "tipo", "label": "Tipo de Grado"},
            ],
        },
        "filter_values_options": {
            "pais": [
                {"value": code, "label": dict(d_countries).get(code, code)}
                for code in Academico.objects.filter(unidad__universidad__pais__isnull=False)
                .values_list("unidad__universidad__pais", flat=True)
                .distinct()
            ],
            "universidad": [
                {"value": uni.id, "label": uni.nombre}
                for uni in (
                    Universidad.objects.filter(
                        id__in=(
                            list(Academico.objects.filter(unidad__isnull=False).values_list("unidad__universidad", flat=True).distinct())
                            + list(
                                GradoInstancia.objects.filter(unidad__isnull=False).values_list("unidad__universidad", flat=True).distinct()
                            )
                        )
                    )
                    .distinct()
                    .order_by("nombre")
                )
            ],
            "tipo": [{"value": tipo[0], "label": tipo[1]} for tipo in GradoInstancia._meta.get_field("tipo").choices],
        },
    }
    return render(request, "front/indicadores.html", context)


def compute_indicadores(request):
    selected_model = request.GET.get("model", "academicos")
    selected_group_criteria = request.GET.get("group_by", "pais")
    selected_filter_criteria = request.GET.get("filter_by", "pais")
    selected_filter_values = request.GET.get("filter_values")

    selected_filter_values = selected_filter_values.split(",") if selected_filter_values else []

    # Model selection
    model_map = {
        "academicos": Academico,
        "universidades": Universidad,
        "grados": GradoInstancia,
    }

    group_map = {
        "academicos": {
            "pais": "unidad__universidad__pais",
            "universidad": "unidad__universidad__nombre",
        },
        "universidades": {
            "pais": "pais",
        },
        "grados": {
            "pais": "unidad__universidad__pais",
            "universidad": "unidad__universidad__nombre",
            "tipo": "tipo",
        },
    }

    filter_map = {
        "academicos": {
            "pais": "unidad__universidad__pais",
            "universidad": "unidad__universidad__id",
        },
        "universidades": {"pais": "pais"},
        "grados": {
            "pais": "unidad__universidad__pais",
            "universidad": "unidad__universidad__id",
            "tipo": "tipo",
        },
    }

    Model = model_map[selected_model]
    group_id = group_map[selected_model][selected_group_criteria]
    filter_field = filter_map[selected_model].get(selected_filter_criteria)

    qs = Model.objects.all()

    # apply filtering (fix: use qs.filter(...))
    if filter_field and selected_filter_values:
        qs = qs.filter(**{f"{filter_field}__in": selected_filter_values})

    qs = qs.distinct()

    # Pre-calc total for percentages
    total_count = qs.count() or 1

    # Aggregations
    qs_count = qs.values(group_id).annotate(count=Count("id")).order_by("-count")
    count_data = [{"key": x[group_id], "count": x["count"]} for x in qs_count]

    qs_percentage = qs.values(group_id).annotate(percentage=Count("id") * 100.0 / total_count).order_by("-percentage")
    percentage_data = [{"key": x[group_id], "percentage": x["percentage"]} for x in qs_percentage]

    # label decoration
    for c, p in zip(count_data, percentage_data):
        key = c["key"]

        if selected_group_criteria == "pais":
            label = dict(d_countries).get(key, key)
            c["label"] = p["label"] = label

        elif selected_group_criteria == "universidad":
            uni = Universidad.objects.filter(nombre=key).first()
            sigla = uni.get_sigla if uni and uni.get_sigla else key
            c["label"] = p["label"] = uni.nombre
            c["key"] = sigla

        elif selected_group_criteria == "tipo":
            tipo_dict = dict(GradoInstancia._meta.get_field("tipo").choices)
            label = tipo_dict.get(key, key)
            c["label"] = p["label"] = label

    # detailed data for downloading
    objects_qs = build_serialized_data(selected_model, qs, group_id)

    return JsonResponse(
        {
            "count_data": count_data,
            "percentage_data": percentage_data,
            "objects_qs": list(objects_qs),
        }
    )
