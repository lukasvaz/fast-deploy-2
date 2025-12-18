import httpx
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DataError, Error, IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django_countries import countries as d_countries

from universidad.models import SecretarioInstitucion, Unidad

from .models import GradoInstancia, ValidationStates


async def validate_url(row, web_field, keyword=None):
    url = row.get(web_field)
    errors = []
    if not url:
        errors.append("La URL está vacía")
        return errors
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0"}, verify=False) as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                errors.append(f"La URL respondió con el estado {response.status_code}")
    except Exception as e:
        errors.append(f"Error al consultar la URL: {str(e)}")
    return errors


def grado_new(request):
    if request.method == "POST":
        # permission checking
        unidad_id = request.POST.get("InputUnidad")
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")
        if not request.user.is_superuser:
            try:
                unidad_obj = Unidad.objects.get(id=unidad_id)
                _ = SecretarioInstitucion.objects.filter(institucion=unidad_obj.universidad).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")
        else:
            try:
                unidad_obj = Unidad.objects.get(id=unidad_id)
            except ObjectDoesNotExist:
                messages.error(request, "Unidad inexistente.")
                is_valid = False

        is_valid = True
        error_required_field = []
        # Nombre is required
        nombre = request.POST.get("InputNombre", "").strip()
        if not nombre:
            error_required_field.append("Nombre")
            is_valid = False
        elif len(nombre) > 200:
            messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
            is_valid = False

        # Tipo is required (optional: adjust as needed)
        tipo = request.POST.get("InputTipo", "").strip()
        if not tipo:
            error_required_field.append("Tipo")
            is_valid = False

        # Optional fields
        nombre_es = request.POST.get("InputNombreEs", "").strip()
        web_site = request.POST.get("InputWeb", "").strip() or None
        fecha_creacion = request.POST.get("InputFecha", None) or None
        activo = bool(request.POST.get("InputActivo", False))

        # Required fields error message
        if error_required_field:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                with transaction.atomic():
                    grado_new_obj = GradoInstancia(
                        unidad=unidad_obj,
                        nombre=nombre,
                        nombre_es=nombre_es,
                        tipo=tipo,
                        web_site=web_site,
                        fecha_creacion=fecha_creacion,
                        activo=activo,
                    )
                    grado_new_obj.save()
            except IntegrityError:
                messages.error(request, "Error de integridad")
            except DataError:
                messages.error(request, "Error en algún campo.")
            except Error as error_msg_db:
                messages.error(request, error_msg_db)
            else:
                return redirect("front:grado", id_grado=grado_new_obj.id)

        return redirect("front:institucion", id_institucion=unidad_obj.universidad.id)

    else:
        raise PermissionDenied


def grado_edit(request, id_grado):
    # Only allow staff to edit (adjust as needed)
    grado_obj = get_object_or_404(GradoInstancia, id=id_grado)

    # check permissions
    has_secretario_permission = SecretarioInstitucion.objects.filter(
        user=request.user,
        institucion=grado_obj.unidad.universidad,
    ).exists()
    if not request.user.is_superuser and not has_secretario_permission:
        return redirect("front:grado", id_grado=grado_obj.id)

    if request.method == "POST":
        grado_obj.nombre_en = request.POST.get("InputNombre", grado_obj.nombre_en)
        grado_obj.tipo = request.POST.get("InputTipo", grado_obj.tipo)
        if request.POST.get("InputWeb") and request.POST.get("InputWeb") != grado_obj.web_site:
            grado_obj.web_site = request.POST.get("InputWeb")
            grado_obj.verification_state = ValidationStates.PENDING
        if not request.POST.get("InputWeb") and request.POST.get("InputWeb") != grado_obj.web_site:
            grado_obj.web_site = None
            grado_obj.verification_state = ValidationStates.INVALID_URL

        grado_obj.fecha_creacion = (
            request.POST.get("InputFecha", grado_obj.fecha_creacion) if request.POST.get("InputFecha", grado_obj.fecha_creacion) else None
        )
        grado_obj.activo = bool(request.POST.get("InputActivo", grado_obj.activo))
        grado_obj.nombre_es = request.POST.get("InputNombreEs", grado_obj.nombre_es)
        unidad_id = request.POST.get("InputUnidadId", "")
        if unidad_id:
            unidad_obj = Unidad.objects.filter(id=unidad_id).first()
            grado_obj.unidad = unidad_obj
        grado_obj.save()
        return redirect("front:grado", id_grado=grado_obj.id)
    if request.method == "GET":
        unidad = grado_obj.unidad
        universidad = unidad.universidad if unidad else None
        tipo_choices = GradoInstancia._meta.get_field("tipo").choices
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
            "grado": grado_obj,
            "unidad": grado_obj.unidad,
            "universidad": universidad,
            "unidades_context": unidades_context,
            "header_text": "Editar Programa",
            "tipo_choices": tipo_choices,
        }
        return render(request, "front/grado_edit.html", context)


def grado_delete(request):
    # check request method
    if request.method != "POST":
        raise PermissionDenied
    # get grado
    grado_id = request.POST.get("grado_id", "")
    if not grado_id:
        messages.error(request, "Error inesperado con los datos enviados.")
        return redirect("front:index")
    try:
        grado_obj = GradoInstancia.objects.get(id=grado_id)
        unidad_obj = grado_obj.unidad
    except ObjectDoesNotExist:
        messages.error(request, "Grado no encontrado.")
        return redirect("front:index")

    # check permissions
    if request.user.is_authenticated:
        has_secretario_permission = SecretarioInstitucion.objects.filter(
            user=request.user,
            institucion=grado_obj.unidad.universidad,
        ).exists()
    else:
        has_secretario_permission = False

    if not request.user.is_superuser and not has_secretario_permission:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect("front:index")

    if not request.user.is_superuser:
        try:
            _ = SecretarioInstitucion.objects.filter(institucion=unidad_obj.universidad).get(user=request.user)
        except ObjectDoesNotExist:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

    try:
        with transaction.atomic():
            grado_obj.delete()
    except IntegrityError:
        messages.error(request, "Error de integridad")
    except DataError:
        messages.error(request, "Error en algún campo.")
    except Error as error_msg_db:
        messages.error(request, error_msg_db)

    return redirect("front:institucion", id_institucion=unidad_obj.universidad.id)
