from django.db.models import F


def build_serialized_data(model_key, qs, group_id):
    # to optimize raw data
    if model_key == "academicos":
        return qs.order_by(group_id).values(
            "nombre",
            "apellido",
            "email",
            "webpage",
            "grado_maximo",
            universidad=F("unidad__universidad__nombre"),
            pais=F("unidad__universidad__pais"),
        )

    elif model_key == "universidades":
        return qs.order_by(group_id).values(
            "nombre",
            "sigla",
            "webpage",
            latitude=F("openalex_institution__openalex_region_latitude"),
            longitude=F("openalex_institution__openalex_region_longitude"),
            city=F("openalex_institution__openalex_city_name"),
            country=F("pais"),
        )

    elif model_key == "grados":
        return qs.order_by(group_id).values(
            "nombre",
            "web_site",
            "tipo",
            universidad=F("unidad__universidad__nombre"),
            pais=F("unidad__universidad__pais"),
        )

    else:
        raise ValueError(f"Unknown model type: {model_key}")
