import re

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import DataError, Error, IntegrityError, models, transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

from grados.models import GradoTipo
from persona.models import CoautorInvestigador, InvestigadorOnDemand, KeywordInvestigador
from persona.services.aminer_client import update_investigador_aminer_data
from persona.services.dblp_client import fetch_name_dblp, update_investigador_dblp_data
from persona.services.openalex_author_client import OpenAlexAuthorClient, update_investigador_openalex_data
from universidad.models import SecretarioInstitucion, Unidad, Universidad

from .models import Academico, AmbitoTrabajo, Area, Subarea


def academico_new(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        institucion_id = int(request.POST["inputInstitucion"])
        academico_new_obj = Academico()
        # Data validation
        is_valid = True

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion__id=institucion_id).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        # Check fields
        error_required_field = []
        if "inputUnidad" in request.POST and request.POST["inputUnidad"] and request.POST["inputUnidad"] != 0:
            unidad_id = request.POST["inputUnidad"]
            try:
                unidad_obj = Unidad.objects.filter(universidad__id=institucion_id).get(id=unidad_id)
                academico_new_obj.unidad = unidad_obj
            except ObjectDoesNotExist:
                messages.error(request, "Unidad inexistente.")
                is_valid = False
        else:
            error_required_field.append("Unidad")
            is_valid = False

        if "inputNombre" in request.POST and request.POST["inputNombre"]:
            nombre = request.POST["inputNombre"]
            if len(nombre) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre) < 5:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                academico_new_obj.nombre = nombre
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "inputApellido" in request.POST and request.POST["inputApellido"]:
            apellido = request.POST["inputApellido"]
            if len(apellido) > 200:
                messages.error(request, "Campo Apellido tiene un largo máximo de 200 caracteres.")
                is_valid = False
            else:
                academico_new_obj.apellido = apellido
        if "inputCorreo" in request.POST and request.POST["inputCorreo"]:
            email = request.POST["inputCorreo"].strip()
            if email:  # Only validate if not empty
                email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
                if len(email) > 320:  # Same limit as frontend
                    messages.error(request, "Correo electrónico demasiado largo.")
                    is_valid = False
                elif not re.match(email_regex, email):
                    messages.error(request, "Formato de correo electrónico inválido.")
                    is_valid = False
                else:
                    academico_new_obj.email = email
        if "inputWebpage" in request.POST and request.POST["inputWebpage"]:
            webpage = request.POST["inputWebpage"].strip()
            if webpage:
                url_regex = r"^(https?:\/\/)?([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,}(?::\d{1,5})?(\/[^\s]*)?$"

                if len(webpage) > 2000:
                    messages.error(request, "Sitio web demasiado largo.")
                    is_valid = False
                elif not re.match(url_regex, webpage):
                    messages.error(request, "Formato de sitio web inválido. Ej: https://example.com")
                    is_valid = False
                else:
                    if not webpage.startswith(("http://", "https://")):
                        webpage = "https://" + webpage
                    academico_new_obj.webpage = webpage

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
                    academico_new_obj.save()

            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

            else:
                return redirect("front:academico", id_academico=academico_new_obj.id)

        return redirect("front:institucion", id_institucion=institucion_id)

    else:
        raise PermissionDenied


def academico_delete(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        academico_id = request.POST.get("academicoId", "")
        unidad_id = request.POST.get("unidadId", "")

        if not academico_id or not unidad_id:
            messages.error(request, "Error inesperado con querystring.")
            return redirect("front:index")

        try:
            unidad_obj = Unidad.objects.get(id=unidad_id)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=unidad_obj.universidad).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        try:
            academico_obj = Academico.objects.filter(unidad=unidad_obj).get(id=academico_id)
        except ObjectDoesNotExist:
            messages.error(request, "Académico no encontrado.")
            return redirect("front:institucion", id_institucion=unidad_obj.universidad.id)

        try:
            with transaction.atomic():
                academico_obj.delete()  # removes associated  models by custom delete

        except IntegrityError:
            messages.error(request, "Error de intregridad")

        except DataError:
            messages.error(request, "Error en algún campo.")

        except Error as error_msg_db:
            messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=unidad_obj.universidad.id)
    else:
        return redirect("front:index")


def academico_change_unidad(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        # Check fields
        if "inputAcademico" not in request.POST or not request.POST["inputAcademico"]:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")
        if "inputUnidadOld" not in request.POST or not request.POST["inputUnidadOld"]:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")
        if "inputUnidadNew" not in request.POST or not request.POST["inputUnidadNew"]:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        try:
            unidad_old_obj = Unidad.objects.get(id=request.POST["inputUnidadOld"])
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=unidad_old_obj.universidad).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        try:
            unidad_new_obj = Unidad.objects.filter(universidad=unidad_old_obj.universidad).get(id=request.POST["inputUnidadNew"])
        except ObjectDoesNotExist:
            messages.error(request, "Unidad no encontrada.")
            return redirect("front:institucion", id_institucion=unidad_old_obj.universidad.id)

        try:
            academico_obj = Academico.objects.filter(unidad=unidad_old_obj).get(id=request.POST["inputAcademico"])
        except ObjectDoesNotExist:
            messages.error(request, "Académico no encontrado.")
            return redirect("front:institucion", id_institucion=unidad_old_obj.universidad.id)

        try:
            academico_obj.unidad = unidad_new_obj
            academico_obj.save()

        except IntegrityError:
            messages.error(request, "Error de intregridad")

        except DataError:
            messages.error(request, "Error en algún campo.")

        except Error as error_msg_db:
            messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=unidad_old_obj.universidad.id)
    else:
        return redirect("front:index")


def academico_update(request, id_academico):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        try:
            academico_ob = Academico.objects.get(id=id_academico)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if not request.user.is_superuser:
            if not (academico_ob.user and academico_ob.user.id == request.user.id):
                try:
                    _ = SecretarioInstitucion.objects.filter(institucion=academico_ob.unidad.universidad).get(user=request.user)
                except ObjectDoesNotExist:
                    messages.error(request, "No tienes permiso para realizar esta acción.")
                    return redirect("front:index")

        # Check fields
        is_valid = True
        error_required_field = []
        if "InputNombre" in request.POST and request.POST["InputNombre"]:
            nombre = request.POST["InputNombre"]
            if len(nombre) > 200:
                messages.error(request, "Campo Nombre tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre) < 2:
                messages.error(request, "Campo Nombre muy corto.")
                is_valid = False
            else:
                academico_ob.nombre = nombre
        else:
            error_required_field.append("Nombre")
            is_valid = False

        if "InputApellido" in request.POST:
            apellido = request.POST["InputApellido"]
            if apellido:
                if len(apellido) > 200:
                    messages.error(request, "Campo Apellido tiene un largo máximo de 200 caracteres.")
                    is_valid = False
                elif len(apellido) < 2:
                    messages.error(request, "Campo Apellido muy corto.")
                    is_valid = False
                else:
                    academico_ob.apellido = apellido
            else:
                academico_ob.apellido = ""

        if "InputEmail" in request.POST:
            email = request.POST["InputEmail"].strip()
            if email:  # Only validate if not empty
                email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

                if len(email) > 320:  # Same limit as frontend
                    messages.error(request, "Correo electrónico demasiado largo.")
                    is_valid = False
                elif not re.match(email_regex, email):
                    messages.error(request, "Formato de correo electrónico inválido.")
                    is_valid = False
                else:
                    academico_ob.email = email
            else:
                # Empty email is allowed
                academico_ob.email = ""

        if "InputWeb" in request.POST:
            webpage = request.POST["InputWeb"].strip()
            if webpage:
                url_regex = r"^(https?:\/\/)?([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,}(?::\d{1,5})?(\/[^\s]*)?$"

                if len(webpage) > 2000:
                    messages.error(request, "Sitio web demasiado largo.")
                    is_valid = False
                elif not re.match(url_regex, webpage):
                    messages.error(request, "Formato de sitio web inválido. Ej: https://example.com")
                    is_valid = False
                else:
                    if not webpage.startswith(("http://", "https://")):
                        webpage = "https://" + webpage
                    academico_ob.webpage = webpage
            else:
                academico_ob.webpage = ""
        if "InputGrado" in request.POST:
            grado = request.POST["InputGrado"]
            if grado:
                if grado in dict(GradoTipo.choices):
                    academico_ob.grado_maximo = grado
                else:
                    messages.error(request, "Campo Grado invalido.")
                    is_valid = False

            else:
                academico_ob.grado_maximo = None

        #  Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        # DBLP
        try:
            if "InputDblp" in request.POST:
                new_dblp_id = request.POST["InputDblp"]
                dblp_regex = r"^[A-Za-z0-9]+/[A-Za-z0-9]+$"
                dblp_validation = True
                investigador_obj = getattr(academico_ob, "investigador_ondemand", None)
                if new_dblp_id:
                    if len(new_dblp_id) > 100:
                        messages.error(request, "DBLP ID demasiado largo.")
                        is_valid = False
                        dblp_validation = False
                    elif not re.match(dblp_regex, new_dblp_id):
                        messages.error(request, "Formato de DBLP ID inválido. Ej: 123/456 o autor/001")
                        is_valid = False
                        dblp_validation = False

                    if dblp_validation:
                        dblp_id = getattr(investigador_obj, "dblp_id", None)
                        if investigador_obj and new_dblp_id != dblp_id:
                            inv_obj, error = update_investigador_dblp_data(academico_ob, new_dblp_id)
                            if not error:
                                academico_ob.dblp_last_fetched_date = timezone.now()
                            else:
                                messages.error(request, error["error"])
                        elif not investigador_obj:
                            with transaction.atomic():
                                ob, error = update_investigador_dblp_data(academico_ob, new_dblp_id)
                                if ob:
                                    academico_ob.investigador_ondemand = ob
                                    academico_ob.save()
                                if error:
                                    academico_ob.investigador_ondemand = None
                                    academico_ob.save()
                else:
                    if getattr(investigador_obj, "dblp_profile", None):
                        investigador_obj.dblp_profile = None
                        CoautorInvestigador.objects.filter(
                            models.Q(investigador_a=investigador_obj) | models.Q(investigador_b=investigador_obj)
                        ).delete()
                        investigador_obj.save()

        except IntegrityError:
            messages.error(request, "Error de intregridad")
            is_valid = False

        # orcid
        try:
            if "InputOrcid" in request.POST:
                new_orcid_id = request.POST["InputOrcid"].strip()
                investigador_obj = getattr(academico_ob, "investigador_ondemand", None)
                orcid_validation = True
                if new_orcid_id:
                    orcid_regex = r"^[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$"
                    if not re.match(orcid_regex, new_orcid_id):
                        messages.error(request, "ORCID ID debe tener formato 0000-0000-0000-0000.")
                        is_valid = False
                        orcid_validation = False
                    if orcid_validation:
                        if investigador_obj and new_orcid_id != investigador_obj.manual_orcid:
                            investigador_obj.manual_orcid = new_orcid_id
                            investigador_obj.save()

                        elif not investigador_obj:
                            with transaction.atomic():
                                investigador_obj = InvestigadorOnDemand(academico=academico_ob)
                                investigador_obj.manual_orcid = new_orcid_id
                                investigador_obj.save()
                                academico_ob.investigador_ondemand = investigador_obj
                else:
                    if investigador_obj and investigador_obj.manual_orcid != "":
                        investigador_obj.manual_orcid = ""
                        investigador_obj.save()

        except IntegrityError:
            messages.error(request, "Error de intregridad")
            is_valid = False
        # aminer id
        try:
            if "InputAminer" in request.POST:
                new_aminer_id = request.POST["InputAminer"].strip()
                inv_obj = getattr(academico_ob, "investigador_ondemand", None)
                current_aminer_id = getattr(getattr(inv_obj, "aminer_profile", None), "aminer_id", None)
                aminer_validation = True
                if new_aminer_id:
                    if len(new_aminer_id) > 50:
                        messages.error(request, "AMiner ID demasiado largo.")
                        is_valid = False
                        aminer_validation = False
                    elif len(new_aminer_id) < 10:
                        messages.error(request, "AMiner ID demasiado corto.")
                        is_valid = False
                        aminer_validation = False
                    if aminer_validation:
                        if new_aminer_id != current_aminer_id:
                            if inv_obj:
                                # update existing InvestigadorOnDemand
                                inv_obj, error = update_investigador_aminer_data(academico_ob, new_aminer_id)
                                if error:
                                    messages.error(request, error["error"])
                            else:

                                ob, error = update_investigador_aminer_data(academico_ob, aminer_id=new_aminer_id)
                                if ob:
                                    academico_ob.investigador_ondemand = ob
                                    academico_ob.save()
                                elif error:
                                    academico_ob.investigador_ondemand = None
                                    academico_ob.save()
                                    messages.error(request, error["error"])

                            academico_ob.aminer_last_fetched_date = timezone.now()
                            academico_ob.save()
                else:
                    if current_aminer_id:
                        if inv_obj and inv_obj.aminer_profile:
                            inv_obj.aminer_profile = None
                            inv_obj.save()
                            KeywordInvestigador.update_investigador_keywords(inv_obj)

        except IntegrityError:
            messages.error(request, "Error de intregridad")
            is_valid = False
        # OpenAlex
        try:
            with transaction.atomic():
                if "inputOpenAlex" in request.POST:
                    new_openalex_id = request.POST["inputOpenAlex"]
                    if new_openalex_id:  # Only validate if not empty
                        openalex_regex = r"^[A-Za-z0-9]{5,20}$"
                        if not re.match(openalex_regex, new_openalex_id):
                            messages.error(request, "OpenAlex ID debe ser alfanumérico con 5-20 caracteres.")
                            is_valid = False
                        else:
                            if new_openalex_id != academico_ob.investigador_ondemand.openalex_id and new_openalex_id != "0":
                                if academico_ob.investigador_ondemand:
                                    inv_obj, error = update_investigador_openalex_data(academico_ob, new_openalex_id)
                                    if error:
                                        messages.error(request, error["error"])
                                else:
                                    with transaction.atomic():
                                        investigador_obj = InvestigadorOnDemand(academico=academico_ob)
                                        ob, error = update_investigador_openalex_data(academico_ob, openalex_id=new_openalex_id)
                                        if ob:
                                            academico_ob.investigador_ondemand = ob
                                            academico_ob.save()
                                        if error:
                                            academico_ob.investigador_ondemand = None
                    else:
                        if getattr(academico_ob.investigador_ondemand, "openalex_profile", None):
                            academico_ob.investigador_ondemand.openalex_profile = None
                            academico_ob.investigador_ondemand.save()
        except Exception as e:
            messages.error(request, e.args[0])
            is_valid = False
        # update unidad
        try:
            if "InputUnidadId" in request.POST and request.POST["InputUnidadId"]:
                new_unidad_id = request.POST["InputUnidadId"]
                if str(academico_ob.unidad.id) != str(new_unidad_id):
                    try:
                        new_unidad_obj = Unidad.objects.get(id=new_unidad_id)
                        academico_ob.unidad = new_unidad_obj
                    except ObjectDoesNotExist:
                        messages.error(request, "Unidad no encontrada.")
                        is_valid = False
        except IntegrityError:
            messages.error(request, "Error de intregridad")
            is_valid = False

        if is_valid:
            try:
                with transaction.atomic():
                    # Areas
                    areas = request.POST["InputAreas"][1:].split(";") if request.POST["InputAreas"] else []
                    subareas = request.POST["InputSubareas"][1:].split(";") if request.POST["InputSubareas"] else []

                    ambitos = AmbitoTrabajo.objects.filter(academico=academico_ob).exclude(deleted=True)
                    subareas_old = []
                    # dealing with old ambitos
                    for ambito in ambitos:
                        # Remove unwanted old ambitos
                        if ambito.subarea.id not in subareas or ambito.subarea.area.id not in areas:
                            ambito.delete()
                        # Keep old ambitos
                        else:
                            subareas_old.append(ambito.subarea)

                    # Add new ambitos
                    subareas_new = Subarea.objects.filter(id__in=subareas).filter(area__id__in=areas).exclude(id__in=subareas_old)
                    # adding Other if area is not represented by any subarea
                    new_areas_ids = [subarea.area.id for subarea in subareas_new]
                    for area_id in areas:
                        if int(area_id) not in new_areas_ids:
                            other_subarea_qs = Subarea.objects.get(area__id=area_id, nombre__in=["Otro", "Other"])
                            subareas_new = subareas_new | Subarea.objects.filter(id=other_subarea_qs.id)

                    subareas_deleteds = [a.subarea for a in AmbitoTrabajo.objects.filter(academico=academico_ob).filter(deleted=True)]
                    # Reactivate deleted ambitos or create new ones
                    for subarea_new_obj in subareas_new:
                        if subarea_new_obj in subareas_deleteds:
                            ambito_removed = AmbitoTrabajo.objects.filter(academico=academico_ob).filter(subarea=subarea_new_obj)[0]
                            ambito_removed.deleted = False
                            ambito_removed.manual = True
                            ambito_removed.save()
                        else:
                            ambito_new = AmbitoTrabajo(
                                academico=academico_ob,
                                subarea=subarea_new_obj,
                                manual=True,
                                deleted=False,
                            )
                            ambito_new.save()

                    # Save
                    academico_ob.save()

            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)
        return redirect("front:academico", id_academico=academico_ob.id)

    else:
        raise PermissionDenied


def reload_academico(request, id_academico):
    """
    DEPRECATED : takes too long to execute as a query endpoint, cronjobs will handle these cases
    """
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        try:
            academico_ob = Academico.objects.get(id=id_academico)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if not request.user.is_superuser:
            if not (academico_ob.user and academico_ob.user.id == request.user.id):
                try:
                    _ = SecretarioInstitucion.objects.filter(institucion=academico_ob.unidad.universidad).get(user=request.user)
                except ObjectDoesNotExist:
                    messages.error(request, "No tienes permiso para realizar esta acción.")
                    return redirect("front:index")

        try:
            # Usuarios externos
            if academico_ob.investigador_ondemand.dblp_id:
                dblp_id = academico_ob.investigador_ondemand.dblp_id
                inv_obj, _ = update_investigador_dblp_data(academico_ob, dblp_id)
                _ = update_investigador_aminer_data(academico_ob.investigador_ondemand)

        except IntegrityError:
            messages.error(request, "Error de intregridad")

        except DataError:
            messages.error(request, "Error en algún campo.")

        except Error as error_msg_db:
            messages.error(request, error_msg_db)

        return redirect("front:academico", id_academico=academico_ob.id)
    else:
        raise PermissionDenied


def reload_institucion(request, id_institucion):
    """
    **DEPRECATED**: takes too long to execute as a query endpoint, cronjobs will handle these cases
    Recarga la información de todos los académicos de una institución
    a partir de sus identificadores en DBLP y AMiner.
    Solo puede ser ejecutada por superusuarios o secretarios de la institución.
    """
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        try:
            institucion_ob = Universidad.objects.get(id=id_institucion)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if not request.user.is_superuser:
            try:
                _ = SecretarioInstitucion.objects.filter(institucion=institucion_ob).get(user=request.user)
            except ObjectDoesNotExist:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect("front:index")

        academicos_query = Academico.objects.filter(unidad__universidad=institucion_ob).all()
        for academico_obj in academicos_query:
            try:
                # Usuarios externos
                if academico_obj.investigador_ondemand and academico_obj.investigador_ondemand.dblp_id:
                    inv_obj, _ = update_investigador_dblp_data(academico_obj)
                    _ = update_investigador_aminer_data(academico_obj)

            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:institucion", id_institucion=id_institucion)
    else:
        raise PermissionDenied


def subarea_action(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        subarea_id = int(request.POST["subareaID"])
        area_id = int(request.POST["areaID"])
        action = request.POST["action"]

        try:
            subarea_obj = Subarea.objects.filter(area__id=area_id).get(id=subarea_id)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        if action == "edit":
            # Data validation
            is_valid = True

            # Check fields
            error_required_field = []
            if "subareaNombreEs" in request.POST and request.POST["subareaNombreEs"]:
                nombre_es = request.POST["subareaNombreEs"]
                if len(nombre_es) > 200:
                    messages.error(request, "Campo Nombre (Español) tiene un largo máximo de 200 caracteres.")
                    is_valid = False
                elif len(nombre_es) < 2:
                    messages.error(request, "Campo Nombre (Español) muy corto.")
                    is_valid = False
                else:
                    subarea_obj.nombre_es = nombre_es
            else:
                error_required_field.append("Nombre (Español)")
                is_valid = False

            if "subareaNombreEn" in request.POST and request.POST["subareaNombreEn"]:
                nombre_en = request.POST["subareaNombreEn"]
                if len(nombre_en) > 200:
                    messages.error(request, "Campo Nombre (Inglés) tiene un largo máximo de 200 caracteres.")
                    is_valid = False
                elif len(nombre_en) < 2:
                    messages.error(request, "Campo Nombre (Inglés) muy corto.")
                    is_valid = False
                else:
                    subarea_obj.nombre_en = nombre_en
            else:
                error_required_field.append("Nombre (Inglés)")
                is_valid = False

            # Required fields
            if len(error_required_field) > 0:
                error_msg = ", ".join(error_required_field)
                if len(error_required_field) == 1:
                    messages.error(request, f"Campo {error_msg} es requerido.")
                else:
                    messages.error(request, f"Los campos {error_msg} son requeridos.")

            if is_valid:
                try:
                    with transaction.atomic():
                        subarea_obj.save()
                except IntegrityError:
                    messages.error(request, "Error de intregridad")

                except DataError:
                    messages.error(request, "Error en algún campo.")

                except Error as error_msg_db:
                    messages.error(request, error_msg_db)

            return redirect("front:areas")

        elif action == "remove":
            try:
                subarea_obj.delete()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)
            return redirect("front:areas")

        else:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")
    else:
        raise PermissionDenied


def subarea_new(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")
        if not request.user.is_superuser:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect("front:index")

        area_id = int(request.POST["areaID"])

        try:
            area_obj = Area.objects.get(id=area_id)
        except ObjectDoesNotExist:
            messages.error(request, "Error inesperado.")
            return redirect("front:index")

        # Data validation
        is_valid = True

        subarea_new_obj = Subarea(area=area_obj)

        # Check fields
        error_required_field = []
        if "subareaNombreEs" in request.POST and request.POST["subareaNombreEs"]:
            nombre_es = request.POST["subareaNombreEs"]
            if len(nombre_es) > 200:
                messages.error(request, "Campo Nombre (Español) tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre_es) < 2:
                messages.error(request, "Campo Nombre (Español) muy corto.")
                is_valid = False
            else:
                subarea_new_obj.nombre_es = nombre_es
        else:
            error_required_field.append("Nombre (Español)")
            is_valid = False

        if "subareaNombreEn" in request.POST and request.POST["subareaNombreEn"]:
            nombre_en = request.POST["subareaNombreEn"]
            if len(nombre_en) > 200:
                messages.error(request, "Campo Nombre (Inglés) tiene un largo máximo de 200 caracteres.")
                is_valid = False
            elif len(nombre_en) < 2:
                messages.error(request, "Campo Nombre (Inglés) muy corto.")
                is_valid = False
            else:
                subarea_new_obj.nombre_en = nombre_en
        else:
            error_required_field.append("Nombre (Inglés)")
            is_valid = False

        # Required fields
        if len(error_required_field) > 0:
            error_msg = ", ".join(error_required_field)
            if len(error_required_field) == 1:
                messages.error(request, f"Campo {error_msg} es requerido.")
            else:
                messages.error(request, f"Los campos {error_msg} son requeridos.")

        if is_valid:
            try:
                with transaction.atomic():
                    subarea_new_obj.save()
            except IntegrityError:
                messages.error(request, "Error de intregridad")

            except DataError:
                messages.error(request, "Error en algún campo.")

            except Error as error_msg_db:
                messages.error(request, error_msg_db)

        return redirect("front:areas")

    else:
        raise PermissionDenied


def academico_get_openalex_suggestions(request):
    if request.method == "GET":
        if request.user.is_anonymous:
            return JsonResponse({"status": "error", "message": "No tienes permiso para realizar esta acción."}, status=403)

        academico_id = request.GET.get("academicoId")
        if not academico_id:
            return JsonResponse({"status": "error", "message": "Error inesperado."}, status=400)

        try:
            academico_obj = Academico.objects.get(id=academico_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "Académico inexistente."}, status=400)

        # Fetch suggestions from OpenAlex API
        try:
            openalex_client = OpenAlexAuthorClient()
            openalex_objects = openalex_client.fetch_suggested_authors(academico_obj)
            cleaned_fields = [
                {"openalex_id": item.get("openalex_id"), "openalex_display_name": item.get("openalex_display_name")}
                for item in openalex_objects
            ]
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error fetching suggestions: {e}"}, status=500)

        return JsonResponse({"status": "success", "suggestions": cleaned_fields}, status=200)


def academico_get_dblp_suggestions(request):
    if request.method == "GET":
        if request.user.is_anonymous:
            return JsonResponse({"status": "error", "message": "No tienes permiso para realizar esta acción."}, status=403)

        academico_id = request.GET.get("academicoId")
        if not academico_id:
            return JsonResponse({"status": "error", "message": "Error inesperado."}, status=400)

        try:
            academico_obj = Academico.objects.get(id=academico_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "Académico inexistente."}, status=400)

        # Fetch suggestions from DBLP API
        try:
            response = fetch_name_dblp(academico_obj.get_full_name_normalized(), with_names=True)
            if "error" in response and response["error"]:
                return JsonResponse({"status": "error", "error": response["error"]}, status=200)
            else:
                cleaned_response = []
                for dblp_id, name in zip(response.get("dblp_ids", []), response.get("names", [])):
                    cleaned_response.append({"dblp_id": dblp_id, "nombre": name})
                response = {"dblp_cand": cleaned_response}

        except Exception as e:
            print("error", e)

        return JsonResponse({"status": "success", "dblp_cand": cleaned_response}, status=200)
    else:
        return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)
