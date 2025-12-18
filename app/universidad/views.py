from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DataError, Error, IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from grados.models import GradoInstancia
from persona.models import Academico
from universidad.services.openalex_institution_client import OpenAlexInstitutionClient
from universidad.services.ror_institution_client import RorInstitutionClient

from .models import OpenAlexInsitution, SecretarioInstitucion, Unidad, Universidad


def institucion_new(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        unviersidad_new = Universidad()
        # Data validation
        is_valid = True

        # Check fields
        error_required_field = []
        if "inputNombre" in request.POST and request.POST["inputNombre"]:
            if len(request.POST["inputNombre"]) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(request.POST["inputNombre"]) < 5:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                unviersidad_new.nombre = request.POST["inputNombre"]
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "inputSigla" in request.POST and request.POST["inputSigla"]:
            if len(request.POST["inputSigla"]) > 10:
                messages.error(request, "Campo Sigla tiene un largo máximo de 10 caracteres.")
                is_valid = False
            elif len(request.POST["inputSigla"]) <= 1:
                messages.error(request, "Campo Sigla tiene un largo mínimo de 2 caracteres.")
                is_valid = False
            else:
                unviersidad_new.sigla = request.POST["inputSigla"]

        if "inputWebpage" in request.POST and request.POST["inputWebpage"]:
            unviersidad_new.webpage = request.POST["inputWebpage"]

        if "inputPais" in request.POST and request.POST["inputPais"] and request.POST["inputPais"] != "0":
            if len(request.POST["inputPais"]) != 2:
                messages.error(request, "Campo País invalido.")
                is_valid = False
            else:
                unviersidad_new.pais = request.POST["inputPais"]
        else:
            error_required_field.append("País")
            is_valid = False

        # file_escudo = ""
        # if "inputFileEscudo" in request.POST:
        #     file_escudo = request.POST["inputFileEscudo"]

        if "inputIDROR" in request.POST and request.POST["inputIDROR"]:
            if len(request.POST["inputIDROR"]) > 20:
                messages.error(request, "Campo ROR ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                unviersidad_new.id_ror = request.POST["inputIDROR"]

        if "inputIDCrossref" in request.POST and request.POST["inputIDCrossref"]:
            if len(request.POST["inputIDCrossref"]) > 20:
                messages.error(request, "Campo Crossref ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                unviersidad_new.id_crossref = request.POST["inputIDCrossref"]

        if "inputIDWikidata" in request.POST and request.POST["inputIDWikidata"]:
            if len(request.POST["inputIDWikidata"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                unviersidad_new.id_wikidata = request.POST["inputIDWikidata"]

        if "inputIDISNI" in request.POST and request.POST["inputIDISNI"]:
            if len(request.POST["inputIDISNI"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                unviersidad_new.id_isni = request.POST["inputIDISNI"]

        if "inputIDRinggold" in request.POST and request.POST["inputIDRinggold"]:
            if len(request.POST["inputIDRinggold"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                unviersidad_new.id_ringgold = request.POST["inputIDRinggold"]

        openalex_ob = None
        if "inputOpenAlex" in request.POST and request.POST["inputOpenAlex"]:
            if len(request.POST["inputOpenAlex"]) > 20:
                messages.error(request, "Campo OpenAlex ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                openalex_id = request.POST["inputOpenAlex"]
                client = OpenAlexInstitutionClient()
                openalex_data = client.fetch_by_openalex_id(openalex_id)
                if openalex_data.get("openalex_id"):
                    openalex_ob = OpenAlexInsitution()
                    for field, value in openalex_data.items():
                        if hasattr(openalex_ob, field):
                            setattr(openalex_ob, field, value)

        #  Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                with transaction.atomic():
                    unviersidad_new.save()
                    if openalex_ob:
                        openalex_ob.universidad = unviersidad_new
                        openalex_ob.save()
                    unviersidad_new.get_or_create_default_unidad()

            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:instituciones")

    else:
        raise PermissionDenied


def institucion_edit(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        if "inputInstitucion" in request.POST and request.POST["inputInstitucion"]:
            try:
                institucion_obj = Universidad.objects.get(id=request.POST["inputInstitucion"])
            except ObjectDoesNotExist:
                messages.error(request, "Institucion inexistente.")
        else:
            messages.error(request, "Error inesperado.")
            return redirect("front:instituciones")

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=institucion_obj).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        # Data validation
        is_valid = True

        # Check fields
        error_required_field = []
        if "inputNombre" in request.POST and request.POST["inputNombre"]:
            if len(request.POST["inputNombre"]) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(request.POST["inputNombre"]) < 5:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                institucion_obj.nombre = request.POST["inputNombre"]
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "inputSigla" in request.POST and request.POST["inputSigla"]:
            if len(request.POST["inputSigla"]) > 10:
                messages.error(request, "Campo Sigla tiene un largo máximo de 10 caracteres.")
                is_valid = False
            elif len(request.POST["inputSigla"]) <= 1:
                messages.error(request, "Campo Sigla tiene un largo mínimo de 2 caracteres.")
                is_valid = False
            else:
                institucion_obj.sigla = request.POST["inputSigla"]
        else:
            error_required_field.append("Sigla")
            is_valid = False

        if "inputWebpage" in request.POST and request.POST["inputWebpage"]:
            institucion_obj.webpage = request.POST["inputWebpage"]

        if "inputPais" in request.POST and request.POST["inputPais"] and request.POST["inputPais"] != "0":
            if len(request.POST["inputPais"]) != 2:
                messages.error(request, "Campo País invalido.")
                is_valid = False
            else:
                institucion_obj.pais = request.POST["inputPais"]
        else:
            error_required_field.append("País")
            is_valid = False

        # file_escudo = ""
        # if "inputFileEscudo" in request.POST:
        #     file_escudo = request.POST["inputFileEscudo"]
        if "inputIDROR" in request.POST:
            if not request.POST["inputIDROR"]:
                institucion_obj.id_ror = None
            elif len(request.POST["inputIDROR"]) > 20:
                messages.error(request, "Campo ROR ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                institucion_obj.id_ror = request.POST["inputIDROR"]

        if "inputIDCrossref" in request.POST:
            if not request.POST["inputIDCrossref"]:
                institucion_obj.id_crossref = None
            elif len(request.POST["inputIDCrossref"]) > 20:
                messages.error(request, "Campo Crossref ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                institucion_obj.id_crossref = request.POST["inputIDCrossref"]

        if "inputIDWikidata" in request.POST:
            if not request.POST["inputIDWikidata"]:
                institucion_obj.id_wikidata = None
            elif len(request.POST["inputIDWikidata"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                institucion_obj.id_wikidata = request.POST["inputIDWikidata"]

        if "inputIDISNI" in request.POST:
            if not request.POST["inputIDISNI"]:
                institucion_obj.id_isni = None
            elif len(request.POST["inputIDISNI"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                institucion_obj.id_isni = request.POST["inputIDISNI"]

        if "inputIDRinggold" in request.POST:
            if not request.POST["inputIDRinggold"]:
                institucion_obj.id_ringgold = None
            elif len(request.POST["inputIDRinggold"]) > 20:
                messages.error(request, "Campo Wikidata ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                institucion_obj.id_ringgold = request.POST["inputIDRinggold"]

        if "inputOpenAlex" in request.POST and request.POST["inputOpenAlex"] != institucion_obj.openalex_id:
            if not request.POST["inputOpenAlex"]:
                try:
                    openalex_instance = OpenAlexInsitution.objects.get(universidad=institucion_obj)
                    openalex_instance.delete()
                except ObjectDoesNotExist:
                    pass
            elif len(request.POST["inputOpenAlex"]) > 20:
                messages.error(request, "Campo OpenAlex ID tiene un largo máximo de 20 caracteres.")
                is_valid = False
            else:
                openalex_id = request.POST["inputOpenAlex"]
                client = OpenAlexInstitutionClient()
                openalex_data = client.fetch_by_openalex_id(openalex_id)
                if openalex_data.get("openalex_id"):
                    openalex_instance, created = OpenAlexInsitution.objects.get_or_create(universidad=institucion_obj)
                    for field, value in openalex_data.items():
                        if hasattr(openalex_instance, field):
                            setattr(openalex_instance, field, value)
                    openalex_instance.save()
        #  Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                institucion_obj.save()

            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=institucion_obj.id)

    else:
        raise PermissionDenied


def institucion_delete(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        if "inputInstitucion" in request.POST and request.POST["inputInstitucion"]:
            try:
                institucion_obj = Universidad.objects.get(id=request.POST["inputInstitucion"])
            except ObjectDoesNotExist:
                messages.error(request, "Institucion inexistente.")
                return redirect("front:instituciones")
        else:
            messages.error(request, "Error inesperado.")
            return redirect("front:instituciones")

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=institucion_obj).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        # Data validation
        is_valid = True

        # Cant remove if academic
        academicos_query = Academico.objects.filter(unidad__universidad=institucion_obj)
        if len(academicos_query) > 0:
            messages.error(request, "No puedes eliminar una Institución que contenga académicos.")
            is_valid = False

        # Cant remove if  grado
        grados_query = GradoInstancia.objects.filter(unidad__universidad=institucion_obj, is_deleted=False)
        if len(grados_query) > 0:
            messages.error(request, "No puedes eliminar una Institución que contenga Programas.")
            is_valid = False

        # Cant remove if unidad
        unidades_query = Unidad.objects.filter(universidad=institucion_obj).filter(is_deleted=False)
        if len(unidades_query) > 0:
            messages.error(request, "No puedes eliminar una Institución que contenga Unidades.")
            is_valid = False

        if is_valid:
            try:
                institucion_obj.delete()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:instituciones")
    else:
        raise PermissionDenied


def institucion_get_openalex_suggestions(request):
    if request.method == "GET":
        if "Insitution_country_code" in request.GET:
            country_code = request.GET.get("Insitution_country_code")
        if "Institution_name" in request.GET:
            name = request.GET.get("Institution_name")
        if Universidad.objects.filter(nombre=name, pais=country_code).exists():
            institution_obj = Universidad.objects.get(nombre=name, pais=country_code)
        else:
            institution_obj = Universidad(nombre=name, pais=country_code)
        # Fetch suggestions from OpenAlex API
        try:
            openalex_client = OpenAlexInstitutionClient()
            openalex_objects = openalex_client.fetch_suggested_institutions(institution_obj)
            cleaned_fields = [
                {
                    "openalex_id": item.get("openalex_id"),
                    "openalex_display_name": item.get("openalex_display_name"),
                    "openalex_country_code": item.get("openalex_country_code"),
                }
                for item in openalex_objects
            ]
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error fetching suggestions: {e}"}, status=500)

        return JsonResponse({"status": "success", "suggestions": cleaned_fields}, status=200)


def institucion_get_ror_suggestions(request):
    if request.method == "GET":
        if "Institution_name" in request.GET:
            name = request.GET.get("Institution_name")

        institution_obj = Universidad(nombre=name)
        # Fetch suggestions from ROR API
        try:
            ror_client = RorInstitutionClient()
            ror_objects = ror_client.fetch_by_name(institution_obj)
            if "error" in ror_objects:
                return JsonResponse({"status": "error", "message": f"Error fetching suggestions: {ror_objects['error']}"}, status=500)
            cleaned_fields = []
            cleaned_fields = []
            for item in ror_objects:
                ror_id = item.get("ror_id")
                ror_names = item.get("ror_names", [])
                ror_name = None
                if ror_names and isinstance(ror_names, list):
                    ror_name = ror_names[0].get("ror_name_value") if "ror_name_value" in ror_names[0] else None

                ror_country_code = None
                location = item.get("ror_locations")
                if location and isinstance(location, list) and len(location) > 0:
                    geo = location[0].get("ror_geo_details")
                    if geo and isinstance(geo, dict):
                        ror_country_code = geo.get("country_code")

                cleaned_fields.append(
                    {
                        "ror_id": ror_id,
                        "ror_name": ror_name,
                        "ror_country_code": ror_country_code,
                    }
                )
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error fetching suggestions: {e}"}, status=500)

        return JsonResponse({"status": "success", "suggestions": cleaned_fields}, status=200)


def unidad_new(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        institucion_id = int(request.POST["inputUniversidad"])
        institucion_obj = get_object_or_404(Universidad, id=institucion_id)

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=institucion_obj).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        unidad_new_obj = Unidad(universidad=institucion_obj)

        # Data validation
        is_valid = True

        # Check fields
        error_required_field = []
        if "inputNombre" in request.POST and request.POST["inputNombre"]:
            nombre = request.POST["inputNombre"]
            if len(nombre) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre) < 2:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                unidad_new_obj.nombre = nombre
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "inputSigla" in request.POST and request.POST["inputSigla"]:
            sigla = request.POST["inputSigla"]
            if len(sigla) > 10:
                messages.error(request, "Campo Sigla tiene un largo máximo de 10 caracteres.")
                is_valid = False
            elif len(sigla) < 2:
                messages.error(request, "Campo Sigla muy corto.")
                is_valid = False
            else:
                unidad_new_obj.sigla = sigla

        if "inputWebpage" in request.POST and request.POST["inputWebpage"]:
            webpage = request.POST["inputWebpage"]
            unidad_new_obj.webpage = webpage

        #  Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                with transaction.atomic():
                    unidad_new_obj.save()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=institucion_id)
    else:
        raise PermissionDenied


def unidad_edit(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        institucion_id = int(request.POST["inputUniversidad"])
        unidad_id = int(request.POST["inputUnidad"])
        unidad_obj = get_object_or_404(Unidad, id=unidad_id)

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=unidad_obj.universidad).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        # Data validation
        is_valid = True

        # Check fields
        error_required_field = []
        if "inputNombre" in request.POST and request.POST["inputNombre"]:
            nombre = request.POST["inputNombre"]
            if len(nombre) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre) < 2:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                unidad_obj.nombre = nombre
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "inputSigla" in request.POST and request.POST["inputSigla"]:
            sigla = request.POST["inputSigla"]
            if len(sigla) > 10:
                messages.error(request, "Campo Sigla tiene un largo máximo de 10 caracteres.")
                is_valid = False
            elif len(sigla) < 2:
                messages.error(request, "Campo Sigla muy corto.")
                is_valid = False
            else:
                unidad_obj.sigla = sigla
        else:
            error_required_field.append("Sigla")
            is_valid = False

        if "inputWebpage" in request.POST and request.POST["inputWebpage"]:
            webpage = request.POST["inputWebpage"]
            unidad_obj.webpage = webpage

        #  Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                with transaction.atomic():
                    unidad_obj.save()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=institucion_id)
    else:
        raise PermissionDenied


def unidad_delete(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        # Data validation
        institucion_id = int(request.POST["inputUniversidad"])
        unidad_id = int(request.POST["inputUnidad"])
        unidad_obj = get_object_or_404(Unidad, id=unidad_id)

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=unidad_obj.universidad).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        is_valid = True

        # Cant remove if academic
        academicos_query = Academico.objects.filter(unidad=unidad_obj)
        if len(academicos_query) > 0:
            messages.error(request, "No puedes eliminar una Unidad que contenga académicos.")
            is_valid = False

        # # Cant remove if is the only Unidad
        # unidades_query = Unidad.objects.filter(universidad=institucion_id).filter(is_deleted=False)
        # if len(unidades_query) == 1:
        #     messages.error(request, 'No puede existir una Institución sin Unidad')
        #     is_valid = False

        if is_valid:
            try:
                with transaction.atomic():
                    unidad_obj.is_deleted = True
                    # unidad_obj.save()
                    unidad_obj.delete()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=institucion_id)
    else:
        raise PermissionDenied
