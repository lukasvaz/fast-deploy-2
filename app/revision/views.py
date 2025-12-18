import json

from django.contrib.postgres.search import TrigramSimilarity
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django_countries import countries as d_countries

from grados.models import GradoInstancia
from persona.models import Academico
from universidad.models import Unidad, Universidad

from .models import CorruptedAcademicoEntry, CorruptedGradoEntry, CorruptedType


def interfaz_revision(request):
    if not request.user.is_superuser:
        return render(request, "front/index.html", status=403)
    if request.method != "GET":
        return render(request, "front/index.html", status=403)
    corrupted_academicos_entries = CorruptedAcademicoEntry.objects.all()
    corrupted_grados_entries = CorruptedGradoEntry.objects.all()
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

    return render(
        request,
        "front/revision.html",
        {
            "corrupted_academicos_entries": corrupted_academicos_entries,
            "corrupted_grados_entries": corrupted_grados_entries,
            "invalid_types": CorruptedType.choices,
            "unidades_context": unidades_context,
        },
    )


def delete_corrupted_academico(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    entry_id = request.POST.get("id")
    try:
        obj = CorruptedAcademicoEntry.objects.get(id=entry_id)
        obj.delete()
        return JsonResponse({"status": "success"})
    except CorruptedAcademicoEntry.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Academico no encontrado"}, status=404)


def delete_corrupted_grado(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    entry_id = request.POST.get("id")
    try:
        obj = CorruptedGradoEntry.objects.get(id=entry_id)
        obj.delete()
        return JsonResponse({"status": "success"})
    except CorruptedGradoEntry.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Grado no encontrado"}, status=404)


def search_universidades(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    # Fuzzy match by nombre and sigla, similar to buscar view
    universidades_objs = (
        Universidad.objects.filter(is_deleted=False)
        .annotate(similarity=TrigramSimilarity("nombre", query))
        .filter(similarity__gt=0.15)
        .order_by("-similarity")
    )

    universidades_by_sigla = (
        Universidad.objects.filter(is_deleted=False)
        .annotate(similarity=TrigramSimilarity("sigla", query))
        .filter(similarity__gt=0.4)
        .exclude(id__in=[u.id for u in universidades_objs])
        .order_by("-similarity")
    )

    universidades_objs |= universidades_by_sigla

    for u in universidades_objs:
        u.unidades = list(u.unidades_set.values("id", "nombre"))

    # Collect all unidades from matched universidades
    unidades = []
    for u in universidades_objs:

        for unidad in u.unidades_set.values("id", "nombre"):
            unidades.append(
                {
                    "unidad_id": unidad["id"],
                    "unidad_nombre": unidad["nombre"],
                    "universidad_nombre": u.nombre,
                    "pais_nombre": u.pais.name,
                }
            )

    return JsonResponse({"results": unidades})


def correct_grado(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    entry_id = request.POST.get("id")
    unidad_id = request.POST.get("unidad_id")
    if not entry_id or not unidad_id:
        return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)
    try:
        with transaction.atomic():
            unidad = Unidad.objects.get(id=unidad_id)
            corrupted = CorruptedGradoEntry.objects.get(id=entry_id)
            GradoInstancia.objects.create(
                nombre=corrupted.nombre,
                nombre_es=corrupted.nombre_es,
                web_site=corrupted.web_site,
                tipo=corrupted.tipo,
                unidad=unidad,
                fecha_creacion=corrupted.created_date,
                activo=corrupted.activo,
            )
            corrupted.delete()
        return JsonResponse({"status": "success"})
    except Unidad.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Unidad no encontrada"}, status=404)
    except CorruptedGradoEntry.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Grado corrupto no encontrado"}, status=404)


def correct_academico(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    entry_id = request.POST.get("id")
    unidad_id = request.POST.get("unidad_id")
    if not entry_id or not unidad_id:
        return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)
    try:
        with transaction.atomic():
            unidad = Unidad.objects.get(id=unidad_id)
            corrupted = CorruptedAcademicoEntry.objects.get(id=entry_id)
            academico = Academico.objects.create(
                nombre=corrupted.nombre,
                apellido=corrupted.apellido,
                unidad=unidad,
                webpage=corrupted.webpage,
                email=corrupted.email,
                grado_maximo=corrupted.grado_maximo,
            )
            academico.save()
        # TODO update  external  data
        return JsonResponse({"status": "success"})
    except Unidad.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Unidad no encontrada"}, status=404)
    except CorruptedAcademicoEntry.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Académico corrupto no encontrado"}, status=404)


def bulk_correct_entries(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    try:
        data = json.loads(request.body)
        grados = data.get("grados", [])
        academicos = data.get("academicos", [])
        unidad_id = data.get("unidad_id")
        for grado_id in grados:
            try:
                with transaction.atomic():
                    unidad = Unidad.objects.get(id=unidad_id)
                    corrupted = CorruptedGradoEntry.objects.get(id=grado_id)
                    GradoInstancia.objects.create(
                        nombre=corrupted.nombre,
                        nombre_es=corrupted.nombre_es,
                        web_site=corrupted.web_site,
                        tipo=corrupted.tipo,
                        unidad=unidad,
                        fecha_creacion=corrupted.created_date,
                        activo=corrupted.activo,
                    )
                    corrupted.delete()
            except IntegrityError:
                corrupted.delete()
                continue
        for academico in academicos:
            print(academico)
            try:
                with transaction.atomic():
                    unidad = Unidad.objects.get(id=unidad_id)
                    corrupted = CorruptedAcademicoEntry.objects.get(id=academico)
                    academico = Academico.objects.create(
                        nombre=corrupted.nombre,
                        apellido=corrupted.apellido,
                        unidad=unidad,
                        webpage=corrupted.webpage,
                        email=corrupted.email,
                        grado_maximo=corrupted.grado_maximo,
                    )
                    academico.save()
            except IntegrityError:
                corrupted.delete()
                continue
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def bulk_delete_corrupted_entries(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Acceso denegado"}, status=403)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            grado_ids = data.get("grados", [])
            academico_ids = data.get("academicos", [])

            # Delete grados
            if grado_ids:
                CorruptedGradoEntry.objects.filter(id__in=grado_ids).delete()
            # Delete academicos
            if academico_ids:
                CorruptedAcademicoEntry.objects.filter(id__in=academico_ids).delete()

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
