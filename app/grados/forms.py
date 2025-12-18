from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_file_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError("ERROR:LIMIT SIZE EXCEEDED")


class UploadFileForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(["csv", "xlsx"]), validate_file_size])


class SanitizeDataForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # mapping is a JSON field with this format: {model_field: csv_field_name}
    mapping = forms.JSONField(
        required=True, error_messages={"required": "ERROR: MAPPING IS REQUIRED", "invalid": "ERROR: INVALID JSON FORMAT"}
    )
    file = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(["csv", "xlsx"]), validate_file_size],
        error_messages={"required": "ERROR: FILE IS REQUIRED", "invalid": "ERROR: INVALID FILE FORMAT"},
    )

    def clean_mapping(self):
        mapping = self.cleaned_data.get("mapping")
        if not isinstance(mapping, dict):
            raise ValidationError("ERROR: MAPPING MUST BE A DICTIONARY")

        required_fields = self.get_required_fields()

        missing_fields = [field for field in required_fields if field not in mapping.keys()]

        if missing_fields:
            raise ValidationError(f"ERROR: MISSING REQUIRED FIELDS: {', '.join(missing_fields)}")

        for key, value in mapping.items():
            if not (isinstance(value, str) and not isinstance(value, bool)):
                raise ValidationError(f"ERROR: FIELD '{key}' MUST BE A STRING")
        return mapping


class SanitizeGradoForm(SanitizeDataForm):
    REQUIRED_GRADO_FIELDS = ("nombre", "web_site", "tipo", "pais", "universidad")
    OPTIONAL_GRADO_FIELDS = (
        "nombre_es",
        "fecha_creacion",
    )

    @classmethod
    def get_required_fields(cls):
        return list(cls.REQUIRED_GRADO_FIELDS)

    @classmethod
    def get_optional_fields(cls):
        return list(cls.OPTIONAL_GRADO_FIELDS)

    @staticmethod
    def get_field_tags():
        return {
            "nombre": ["Program Name", "Degree Name", "Nombre Grado", "Nombre Programa"],
            "nombre_es": [
                "Nombre Programa Castellano",
                "Nombre Grado en Castellano",
                "Program Name en Castellano",
                "Degree Name en Castellano",
                "Nombre Programa en Castellano",
            ],
            "pais": ["Pais", "Country", "Pais Universidad", "Country University"],
            "tipo": ["Grado Otorgado", "Degree Granted", "Type", "Tipo"],
            "universidad": ["universidad", "university", "nombreUniversidad", "universityName"],
            "unidad": [
                "Unidad",
                "Academic Unit",
                "Department",
                "Department Name",
                "Institute Name",
                "Institute",
                "Unidad Academica",
                "Facultad",
                "Departamento",
                "Istituto",
            ],
            "fecha_creacion": ["Fecha", "Año", "Date", "Year", "Fecha Creacion", "Year Creation", "Creation Date"],
            "web_site": ["WebPage", "Web Page", "WebSite", "Web Site", "Sitio Web", "Web"],
            "activo": ["Activo", "Active"],
        }

    @staticmethod
    def get_type_tags():
        return {
            # include  portuguese names
            "LIC": ["Licenciatura", "Lic", "Lic.", "Undergraduate", "Bachiller", "Bachelor", "Grado", "Bacharelado", "Bacharel"],
            "MSC": ["Maestría", "Master", "Maestria", "Magister", "Magíster", "Msc", "Masters", "Mestrado"],
            "PHD": ["Doctorado", "Doctorate", "Phd", "PostDoctorate", "Ph.D.", "Doutorado", "Doctorante"],
            "TECH": ["Técnico Superior", "Technician", "Technical"],
        }

    @staticmethod
    def get_field_descriptions():
        return {
            "nombre": "Nombre del grado académico o programa ofrecido por la universidad.",
            "nombre_es": "Nombre del grado académico o programa en español.",
            "pais": "País donde se encuentra la universidad que ofrece el grado.",
            "tipo": "Tipo de grado académico (por ejemplo, Licenciatura, Maestría, Doctorado).",
            "universidad": "Nombre de la universidad que ofrece el grado.",
            "fecha_creacion": "Fecha o año en que se creó o comenzó a ofrecer el grado.",
            "web_site": "URL del sitio web oficial del grado o programa académico.",
        }


class SanitizeAcademicoForm(SanitizeDataForm):
    REQUIRED_ACADEMIC_FIELDS = ("nombre", "universidad", "pais")
    OPTIONAL_ACADEMIC_FIELDS = ("apellido", "webpage", "email", "orcid_id", "grado_maximo")

    @classmethod
    def get_required_fields(cls):
        return list(cls.REQUIRED_ACADEMIC_FIELDS)

    @classmethod
    def get_optional_fields(cls):
        return list(cls.OPTIONAL_ACADEMIC_FIELDS)

    @staticmethod
    def get_field_tags():
        return {
            "nombre": ["Nombre", "Name", "First Name", "Nombre Academico"],
            "apellido": ["Apellido", "Last Name", "Surname", "Apellido Academico"],
            "universidad": ["Universidad", "University", "Nombre Universidad", "University Name"],
            "pais": ["Pais", "Country", "Pais Universidad", "Country University"],
            "webpage": ["WebPage", "Web Page", "WebSite", "Web Site", "Sitio Web", "Web"],
            "email": ["Email", "Correo", "Correo Electronico", "Emmail Academico"],
            "grado_maximo": ["Grado Maximo", "Highest Degree", "Highest Academic Degree", "Academic Degree", "Grado Academico"],
            "orcid_id": ["ORCID", "ORCID ID", "ORCID Identifier", "Identificador ORCID", "ORCID Academico", "orcid_id Academico", "orcid"],
        }

    @staticmethod
    def get_field_descriptions():
        return {
            "nombre": "Nombre del académico.",
            "apellido": "Apellido del académico.",
            "universidad": "Nombre de la universidad a la que está afiliado el académico.",
            "pais": "País donde se encuentra la universidad del académico.",
            "webpage": "URL del sitio web personal o profesional del académico.",
            "email": "Dirección de correo electrónico del académico.",
            "grado_maximo": "El grado académico más alto obtenido por el académico (por ejemplo, Licenciatura, Maestría, Doctorado).",
            "orcid_id": "Identificador ORCID del académico.",
        }


class SanitizeInstitucionForm(SanitizeDataForm):
    REQUIRED_INSTITUCION_FIELDS = ("nombre", "sigla", "pais")
    OPTIONAL_INSTITUCION_FIELDS = ["webpage"]

    @classmethod
    def get_required_fields(cls):
        return list(cls.REQUIRED_INSTITUCION_FIELDS)

    @classmethod
    def get_optional_fields(cls):
        return list(cls.OPTIONAL_INSTITUCION_FIELDS)

    @staticmethod
    def get_field_tags():
        return {
            "nombre": ["Nombre", "Name", "Institution Name", "Nombre Institucion"],
            "sigla": ["Sigla", "Acronym", "Abbreviation", "Institution Acronym", "Institution Abbreviation", "Sigla Institucion"],
            "pais": ["Pais", "Country", "Pais Institucion", "Country Institution"],
        }

    @staticmethod
    def get_field_descriptions():
        return {
            "nombre": "Nombre de la institución académica o de investigación.",
            "pais": "País donde se encuentra la institución.",
            "sigla": "Sigla o acrónimo comúnmente utilizado para referirse a la institución.",
        }
