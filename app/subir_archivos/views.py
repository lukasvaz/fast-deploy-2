import json
from datetime import datetime

from django.db import IntegrityError
from django.http import JsonResponse
from django_countries import countries

from grados.models import GradoInstancia
from persona.models import Academico, InvestigadorOnDemand
from revision.models import CorruptedAcademicoEntry, CorruptedGradoEntry
from subir_archivos.field_sanitizer import AcademicoSanitizer, GradoSanitizer, InstitucionSanitizer
from universidad.models import Universidad


def validate_university_field(row):
    """
    Validate the university name in the specified field by checking its existence in the database.
    Input:
    - row: dict representing a single data row
            { "model_field": "value", ...
            }
    Output:
    - errors: list of error messages (if any)
    - suggested_value: suggested university name (if any)
    - score: similarity score for the suggested value (if any)
    """
    universidad = row.get("universidad")
    pais = row.get("pais")
    if pais and universidad:
        pais_code = countries.by_name(pais.strip())
        errors = []
        suggested_value = None
        score = None
        is_direct = None
        direct = Universidad.objects.filter(pais=pais_code).get_by_name_or_sigla(universidad)
        if not direct:
            fuzzy_universidad, _ = Universidad.objects.filter(pais=pais_code).get_by_name_or_sigla_fuzzy(universidad)
            if not fuzzy_universidad:
                errors.append("Universidad no encontrada")
            else:
                suggested_value = fuzzy_universidad
                is_direct = False
        else:
            suggested_value = direct
            is_direct = True
            score = 1.0
        return errors, suggested_value, is_direct, score
    else:
        return ["País y Universidad son campos requeridos para validar"], None, None, None


def sanitizar_data_grados(request):
    """
    View to sanitize (validate and modify) uploaded CSV data for GradoInstancia entries.
        Input :
        - request.POST file : FILETYPE with data to sanitize
        - request.POST mapping :JSON string mapping CSV columns to model fields
                                 { "model_field": "csv_column", ...
                                 }
        Output contract:

       -Output:
    {
        - status: ENTRY_TYPE , "success" or "error"
        - valid_entries: ENTRY_TYPE, list of sanitized valid rows
        - corrupted_entries: ENTRY_TYPE, list of rows with errors and suggested corrections
        - total: total number of processed rows
    }
    # ENTRY_TYPE:
    {
        - data: dict with mapped model fields and their values
        - errors: list of error objects (for corrupted entries)
        - suggested_value: dict with suggested corrections (if applicable)
        - score: similarity score for suggested corrections (if applicable)
    }
    """
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        mapping = request.POST.get("mapping")
        mapping_dict = json.loads(mapping)
        parsedData = request.POST.get("parsedData")
        parsedData = json.loads(parsedData)

        # Cleaning defined fields
        # decoded = uploaded_file.read().decode('utf-8').splitlines()
        # reader = csv.DictReader(decoded)

        gradoSanitizer = GradoSanitizer(mapping_dict)

        cleaned_rows = []
        for row in parsedData:
            # Replace original field names in the row with their mapped DB field names
            db_mapped_row = {}
            for model_field, csv_field in mapping_dict.items():
                if csv_field and csv_field in row:
                    db_mapped_row[model_field] = row[csv_field]
                else:
                    db_mapped_row[model_field] = ""
            # discard if all empty
            if not any(value for value in db_mapped_row.values()):
                continue

            # Use gradoSanitizer to clean fields
            cleaned_row = gradoSanitizer.clean(db_mapped_row)

            cleaned_rows.append(cleaned_row)

        valid_entries = []
        corrupted_entries = []

        # Prepare async university validation tasks
        # university_tasks = [sync_to_async(validate_university_field)(row) for row in cleaned_rows]
        university_results = [validate_university_field(row) for row in cleaned_rows]

        # Run all validations
        for idx, row in enumerate(cleaned_rows):
            entry_errors = []
            row_response = {"data": row}

            # University validation (from parallel results)
            university_errors, suggested_value, is_direct, score = university_results[idx]
            if suggested_value and suggested_value != row.get("universidad"):
                row_response["suggested_value"] = {
                    "universidad": suggested_value.nombre,
                    "pais": suggested_value.pais.name,
                    "is_direct": is_direct,
                }
            if score:
                row_response["score"] = score
            if university_errors:
                error_obj = {"universidad": {"message": university_errors, "modificable": False}}
                entry_errors.append(error_obj)
            if entry_errors:
                row_response["errors"] = entry_errors
                corrupted_entries.append(row_response)
            else:
                valid_entries.append(row_response)
        return JsonResponse(
            {"status": "success", "valid_entries": valid_entries, "corrupted_entries": corrupted_entries, "total": len(cleaned_rows)}
        )


def sanitizar_data_academico(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        parsedData = request.POST.get("parsedData")
        parsedData = json.loads(parsedData)
        mapping = request.POST.get("mapping")
        mapping_dict = json.loads(mapping)
        # Cleaning defined fields
        cleaned_rows = []
        academicoSanitizer = AcademicoSanitizer(mapping_dict)
        for row in parsedData:
            # Replace original field names in the row with their mapped DB field names
            db_mapped_row = {}
            for model_field, csv_field in mapping_dict.items():
                if csv_field and csv_field in row:
                    db_mapped_row[model_field] = row[csv_field]
                else:
                    db_mapped_row[model_field] = ""

            # Use gradoSanitizer to clean fields
            cleaned_row = academicoSanitizer.clean(db_mapped_row)
            # if all empty
            if not any(value for value in cleaned_row.values()):
                continue
            cleaned_rows.append(cleaned_row)

        # Making async calls to validate rows
        valid_entries = []
        corrupted_entries = []
        # Prepare async university validation tasks
        university_results = [validate_university_field(row) for row in cleaned_rows]
        for idx, row in enumerate(cleaned_rows):
            row_response = {"data": row}
            # get all errors
            entry_errors = []

            # University validation (from parallel results)
            university_errors, suggested_value_university, is_direct, score = university_results[idx]
            # append suggestions
            if suggested_value_university and suggested_value_university != row.get("universidad"):
                row_response["suggested_value"] = {
                    "universidad": suggested_value_university.nombre,
                    "pais": suggested_value_university.pais.name,
                    "is_direct": is_direct,
                }
            # append errors
            if university_errors:
                if university_errors:
                    error_obj = {"universidad": {"message": university_errors, "modificable": False}}
                    entry_errors.append(error_obj)
            if entry_errors:
                row_response["errors"] = entry_errors
                corrupted_entries.append(row_response)
            else:
                valid_entries.append(row_response)
        return JsonResponse(
            {"status": "success", "valid_entries": valid_entries, "corrupted_entries": corrupted_entries, "total": len(cleaned_rows)}
        )


def sanitizar_data_instituciones(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        parsedData = request.POST.get("parsedData")
        parsedData = json.loads(parsedData)
        mapping = request.POST.get("mapping")
        mapping_dict = json.loads(mapping)
        # Cleaning defined fields
        cleaned_rows = []
        academicoSanitizer = InstitucionSanitizer(mapping_dict)
        for row in parsedData:
            # Replace original field names in the row with their mapped DB field names
            db_mapped_row = {}
            for model_field, csv_field in mapping_dict.items():
                if csv_field and csv_field in row:
                    db_mapped_row[model_field] = row[csv_field]
                else:
                    db_mapped_row[model_field] = ""
            # if all empty
            if not any(value for value in db_mapped_row.values()):
                continue
            # Use gradoSanitizer to clean fields
            cleaned_row = academicoSanitizer.clean(db_mapped_row)
            cleaned_rows.append(cleaned_row)

        # Making async calls to validate rows
        valid_entries = []
        corrupted_entries = []
        # Prepare async university validation tasks
        for idx, row in enumerate(cleaned_rows):
            row_response = {"data": row}
            # get all errors
            valid_entries.append(row_response)

        return JsonResponse(
            {"status": "success", "valid_entries": valid_entries, "corrupted_entries": corrupted_entries, "total": len(cleaned_rows)}
        )


def load_data_academicos(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        created_count = 0
        duplicated_count = 0
        try:
            data = json.loads(request.body.decode("utf-8"))
            valid_entries = data.get("valid_entries", [])
            raw_entries = data.get("raw_entries", [])  # same size than valid_entries
            corrupted_entries = data.get("corrupted_entries", [])
            created_entries = []
            duplicated_entries = []

            for raw_entry, entry in zip(raw_entries, valid_entries):
                nombre = entry.get("nombre")
                apellido = entry.get("apellido")
                universidad_nombre = entry.get("universidad")
                pais_nombre = entry.get("pais")
                email = entry.get("email")
                webpage = entry.get("webpage", None)
                grado_maximo = entry.get("grado_maximo", None)
                orcid_id = entry.get("orcid_id", None)
                # Buscar código de país
                pais_code = None
                for code, name in countries:
                    if name.lower() == (pais_nombre or "").lower():
                        pais_code = code
                        break

                # Buscar universidad
                universidad = Universidad.objects.filter(pais=pais_code).get_by_name_or_sigla(universidad_nombre)

                # Crear el académico solo si se encontró la universidad
                try:
                    if universidad:
                        # getting unidad by email
                        if email:
                            unidades_siglas = universidad.unidades_set.values_list("sigla", flat=True)
                            # lowercase comparison
                            domain_options = [option.lower() for option in email.split("@")[-1].split(".")]
                            if any(sigla.lower() in domain_options for sigla in unidades_siglas if sigla):
                                unidad = universidad.unidades_set.filter(sigla__in=domain_options).first()
                            else:
                                unidad = universidad.get_or_create_default_unidad()
                        else:
                            unidad = universidad.get_or_create_default_unidad()

                        academico_obj, academico_created = Academico.objects.get_or_create(
                            nombre=nombre,
                            apellido=apellido,
                            unidad=unidad,
                        )
                        if academico_created:
                            created_count += 1
                            if not academico_obj.email:
                                academico_obj.email = email
                            if webpage and not academico_obj.webpage:
                                academico_obj.web_site = webpage
                            if grado_maximo and not academico_obj.grado_maximo:
                                academico_obj.grado_maximo = grado_maximo
                            if orcid_id:
                                investigador_ob = InvestigadorOnDemand.objects.create(
                                    nombre=nombre, apellido=apellido, manual_orcid=orcid_id
                                )
                                academico_obj.investigador_ondemand = investigador_ob
                            academico_obj.save()
                            created_entries.append(
                                {
                                    "nombre": nombre,
                                    "apellido": apellido,
                                    "original_universidad": raw_entry.get("universidad"),
                                    "matched_universidad": universidad.nombre,
                                    "matched_unidad": unidad.nombre,
                                    "pais": pais_nombre,
                                    "email": email,
                                    "webpage": webpage,
                                    "grado_maximo": grado_maximo,
                                }
                            )
                        else:
                            # Update the existing Academico entry with non-required data IF MISSING
                            if not academico_obj.email:
                                academico_obj.email = email
                            if webpage and not academico_obj.webpage:
                                academico_obj.web_site = webpage
                            if grado_maximo and not academico_obj.grado_maximo:
                                academico_obj.grado_maximo = grado_maximo
                            if orcid_id:
                                if getattr(academico_obj, "investigador_ondemand", None):
                                    if not academico_obj.investigador_ondemand.manual_orcid:
                                        academico_obj.investigador_ondemand.manual_orcid = orcid_id
                                        academico_obj.investigador_ondemand.save()
                                else:
                                    investigador_ob = InvestigadorOnDemand.objects.create(
                                        nombre=nombre, apellido=apellido, manual_orcid=orcid_id
                                    )
                                    academico_obj.investigador_ondemand = investigador_ob
                            academico_obj.save()
                            duplicated_entries.append(
                                {
                                    "nombre": nombre,
                                    "apellido": apellido,
                                    "original_universidad": raw_entry.get("universidad"),
                                    "matched_universidad": universidad.nombre,
                                    "matched_unidad": unidad.nombre,
                                    "pais": pais_nombre,
                                    "email": email,
                                    "webpage": webpage,
                                    "grado_maximo": grado_maximo,
                                }
                            )
                            duplicated_count += 1
                except IntegrityError:
                    duplicated_count += 1
            # Log corrupted entries for manual review
            for i, entry in enumerate(data.get("corrupted_entries", [])):
                nombre = entry.get("nombre")
                apellido = entry.get("apellido")
                universidad_nombre = entry.get("universidad")
                pais_nombre = entry.get("pais")
                grado_maximo = entry.get("grado_maximo", None)
                email = entry.get("email")
                # Buscar código de país
                pais_code = None
                for code, name in countries:
                    if name.lower() == (pais_nombre or "").lower():
                        pais_code = code
                        break
                # safe check just for masive loadings -> unique full_name by pais,
                # even if institution is not  matched, if academico exists in same country will probably be the same
                # to prevent errors -> not added  for revision
                if pais_code:
                    academicos_pais_qs = Academico.objects.filter(unidad__universidad__pais=pais_code).select_related(
                        "unidad", "unidad__universidad"
                    )
                    pais_normalized_names = [academico.get_full_name_normalized() for academico in academicos_pais_qs]
                    query_name_normalized = Academico(nombre=nombre, apellido=apellido).get_full_name_normalized()
                    if query_name_normalized in pais_normalized_names:
                        corrupted_entries[i]["revision"] = "False"
                        continue

                invalid_entry, _ = CorruptedAcademicoEntry.objects.get_or_create(
                    nombre=nombre,
                    apellido=apellido,
                    universidad=universidad_nombre,
                    pais_universidad=pais_nombre,
                    grado_maximo=grado_maximo,
                    email=email,
                    created_by=request.user,
                )
                invalid_entry.save()
                corrupted_entries[i]["revision"] = "True"

            return JsonResponse(
                {
                    "status": "success",
                    "entries_count": created_count,
                    "duplicated_count": duplicated_count,
                    "created_entries": created_entries,
                    "duplicated_entries": duplicated_entries,
                    "corrupted_entries": corrupted_entries,
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


def load_data_grados(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        try:
            created_count = 0
            duplicated_count = 0
            data = json.loads(request.body.decode("utf-8"))
            valid_entries = data.get("valid_entries", [])
            raw_entries = data.get("raw_entries", [])  # same size than valid_entries
            corrupted_entries = data.get("corrupted_entries", [])

            duplicated_entries = []
            created_entries = []

            for raw_entry, entry in zip(raw_entries, valid_entries):
                nombre = entry.get("nombre")
                nombre_es = entry.get("nombre_es", None)
                universidad_nombre = entry.get("universidad")
                pais_nombre = entry.get("pais")
                web_site = entry.get("web_site")
                fecha = entry.get("fecha")
                tipo = entry.get("tipo")

                # Buscar universidad
                universidad = Universidad.objects.get_by_name_or_sigla(universidad_nombre)
                # Crear la instancia de grado solo si se encontró la universidad
                if universidad:
                    # getting unidad
                    if web_site:
                        unidades_siglas = universidad.unidades_set.values_list("sigla", flat=True)
                        # lowercase comparison
                        domain_options = [option.lower() for option in web_site.split(".")]
                        if any(sigla.lower() in domain_options for sigla in unidades_siglas if sigla):
                            unidad = universidad.unidades_set.filter(sigla__in=domain_options).first()
                        else:
                            unidad = universidad.get_or_create_default_unidad()
                    else:
                        unidad = universidad.get_or_create_default_unidad()

                    grado, created = GradoInstancia.objects.get_or_create(
                        nombre=nombre,
                        tipo=tipo,
                        unidad=unidad,
                    )

                    if created:
                        created_count += 1
                        if nombre_es and not grado.nombre_es:
                            grado.nombre_es = nombre_es
                        if web_site and not grado.web_site:
                            grado.web_site = web_site
                        if fecha and not grado.fecha_creacion:
                            grado.fecha_creacion = datetime.strptime(fecha, "%Y-%m-%d")
                        created_entries.append(
                            {
                                "nombre": nombre,
                                "nombre_es": nombre_es,
                                "pais": pais_nombre,
                                "web_site": web_site,
                                "fecha": fecha,
                                "tipo": tipo,
                                "universidad_original": raw_entry.get("universidad"),
                                "universidad_matched": universidad.nombre,
                                "unidad_matched": unidad.nombre,
                            }
                        )

                        grado.save()

                    else:
                        if nombre_es and not grado.nombre_es:
                            grado.nombre_es = nombre_es
                        if web_site and not grado.web_site:
                            grado.web_site = web_site
                        if fecha and not grado.fecha_creacion:
                            grado.fecha_creacion = datetime.strptime(fecha, "%Y-%m-%d")
                        grado.save()

                        duplicated_entries.append(
                            {
                                "nombre": nombre,
                                "nombre_es": nombre_es,
                                "pais": pais_nombre,
                                "web_site": web_site,
                                "fecha": fecha,
                                "tipo": tipo,
                                "universidad_original": universidad_nombre,
                                "universidad_matched": universidad.nombre,
                                "unidad_matched": unidad.nombre,
                            }
                        )
                        duplicated_count += 1

            for entry in corrupted_entries:
                nombre = entry.get("nombre")
                nombre_es = entry.get("nombre_es", None)
                universidad_nombre = entry.get("universidad")
                pais_nombre = entry.get("pais")
                web_site = entry.get("web_site")
                fecha = entry.get("fecha")
                tipo = entry.get("tipo")

                invalid_entry, _ = CorruptedGradoEntry.objects.get_or_create(
                    nombre=nombre,
                    nombre_es=nombre_es,
                    universidad=universidad_nombre,
                    pais_universidad=pais_nombre,
                    web_site=web_site,
                    fecha_creacion=fecha,
                    tipo=tipo,
                    created_by=request.user,
                )
                invalid_entry.save()
            # serializing
            # duplicated_entries= [GradosIndicadoresSerializer(entry).data for entry in duplicated_entries]
            return JsonResponse(
                {
                    "status": "success",
                    "entries_count": created_count,
                    "duplicated_count": duplicated_count,
                    "created_entries": created_entries,
                    "duplicated_entries": duplicated_entries,
                    "corrupted_entries": corrupted_entries,
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


def load_data_instituciones(request):
    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
    if request.method == "POST":
        try:
            created_count = 0
            duplicated_count = 0
            data = json.loads(request.body.decode("utf-8"))
            valid_entries = data.get("valid_entries", [])
            created_entries = []
            corrupted_entries = data.get("corrupted_entries", [])
            duplicated_entries = []

            for entry in valid_entries:
                nombre = entry.get("nombre")
                sigla = entry.get("sigla", None)
                pais_nombre = entry.get("pais")
                web_site = entry.get("web_site", None)

                # Resolve country code
                pais_code = None
                for code, name in countries:
                    if name.lower() == (pais_nombre or "").lower():
                        pais_code = code
                        break

                # Try to find existing Universidad (prefer matching by name/sigla within country if possible)
                universidad = None
                if pais_code:
                    universidad = Universidad.objects.filter(pais=pais_code).get_by_name_or_sigla(nombre)

                    if not universidad:
                        universidad, score = Universidad.objects.filter(pais=pais_code).get_by_name_or_sigla_fuzzy(nombre, 0.7)

                if not universidad:
                    try:
                        universidad, created = Universidad.objects.get_or_create(
                            nombre=nombre,
                            pais=pais_code,
                            defaults={
                                "sigla": sigla or None,
                                "webpage": web_site or None,
                            },
                        )
                        if created:
                            universidad.get_or_create_default_unidad()
                            created_entries.append(
                                {
                                    "original_nombre": nombre,
                                    "original_sigla": sigla,
                                    "original_pais": pais_nombre,
                                }
                            )
                            created_count += 1
                        else:
                            duplicated_entries.append(
                                {
                                    "original_nombre": nombre,
                                    "original_sigla": sigla,
                                    "original_pais": pais_nombre,
                                    "matched_nombre": universidad.nombre,
                                    "matched_pais": universidad.pais,
                                }
                            )
                            duplicated_count += 1
                    except IntegrityError:
                        duplicated_entries.append(
                            {
                                "original_nombre": nombre,
                                "original_sigla": sigla,
                                "original_pais": pais_nombre,
                                "matched_nombre": nombre,
                                "matched_pais": pais_code,
                            }
                        )
                        duplicated_count += 1
                else:
                    # Update missing optional fields if present in the import
                    updated = False
                    if sigla and not getattr(universidad, "sigla", None):
                        universidad.sigla = sigla
                        updated = True
                    if web_site and not getattr(universidad, "webpage", None):
                        universidad.webpage = web_site
                        updated = True

                    if updated:
                        universidad.save()
                    duplicated_entries.append(
                        {
                            "original_nombre": nombre,
                            "original_sigla": sigla,
                            "original_pais": pais_nombre,
                            "matched_nombre": universidad.nombre,
                            "matched_pais": str(universidad.pais),
                        }
                    )
                    duplicated_count += 1

            return JsonResponse(
                {
                    "status": "success",
                    "entries_count": created_count,
                    "duplicated_count": duplicated_count,
                    "created_entries": created_entries,
                    "corrupted_entries": corrupted_entries,
                    "duplicated_entries": duplicated_entries,
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
