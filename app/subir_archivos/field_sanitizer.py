import asyncio
import re
import string
from datetime import datetime

from django_countries import countries

from grados.forms import SanitizeGradoForm
from grados.models import GradoTipo


class FieldCleaner:
    """
    A class to clean, validate, and infer data for a given field.

    Parameters:
    - cleaning_rules: dict of functions, functions meant to alter field in place.
                            {model_field: function}
    - validation_rules: dict of functions , functions meant to return field errors an suggested values.
                            {model_field: async function-> [error],suggested_value}
    - inference_rules: dict of async functions, functions meant to infer new fields.
                            {model_field: async function -> inferred_value}
    """

    def __init__(self, cleaning_rules=None, validation_rules=None, inference_rules=None):
        self.cleaning_rules = cleaning_rules or []
        self.validation_rules = validation_rules or []
        self.inference_rules = inference_rules or []

    def clean(self, row):
        cleaned_row = row.copy()
        for field, func in self.cleaning_rules.items():
            if field in cleaned_row:
                cleaned_row[field] = func(cleaned_row[field])
        return cleaned_row

    async def validate(self, row):
        # Run all validation rules (async)
        results = await asyncio.gather(*(rule(row) for rule in self.validation_rules))
        return results

    async def infer(self, row):
        # Run all inference rules (async)
        results = await asyncio.gather(*(rule(row) for rule in self.inference_rules))
        return results


class AcademicoSanitizer(FieldCleaner):
    def __init__(self, mapping_dict):
        super().__init__(mapping_dict)
        self.cleaning_rules = {
            "nombre": clean_academico_text,
            "apellido": clean_academico_text,
            "pais": clean_pais,
            "grado_maximo": clean_grado_maximo,
            "email": clean_email,
            "orcid_id": clean_orcid_id,
        }


class GradoSanitizer(FieldCleaner):
    def __init__(self, mapping_dict):
        super().__init__(mapping_dict)
        self.cleaning_rules = {
            "tipo": clean_degree_type,
            "nombre": clean_degree_name,
            "pais": clean_pais,
            "fecha_creacion": clean_creation_date,
        }


class InstitucionSanitizer(FieldCleaner):
    def __init__(self, mapping_dict):
        super().__init__(mapping_dict)
        self.cleaning_rules = {"pais": clean_pais, "nombre": clean_degree_name, "sigla": clean_sigla}


# cleaning functions for academicos
def clean_academico_text(text):
    for char in [".", ",", "-", "Dr. ", "Dra.", "Lic. ", "Ing. ", "MSc.", "PhD. "]:
        text = re.sub(re.escape(char), " ", text, flags=re.IGNORECASE)
    return " ".join(word.capitalize() for word in text.strip().split() if len(word) > 1)  # len(word)>1 to avoid single letter words like L.


def clean_grado_maximo(grado):
    """
    Clean the grado_maximo field to match the GRADOS codes.
    """
    GRADO_MAXIMO_TAGS = {
        "Phd": ["phd", "doctorado", "dr", "doctor", "ph.d", "doctorante", "doc"],
        "Master": ["master", "magíster", "magister", "msc", "maestria", "maestría", "maestro"],
        "Graduate": ["licenciado", "ingeniero", "graduate", "licenciatura", "ingenieria", "ing", "lic"],
        "Bachelor": ["bachiller", "bachelor", "universitario", "universidad"],
        "Technician": ["técnico", "tecnico", "technician"],
    }
    if not grado:
        return None
    grado_norm = grado.strip().lower()
    for code, tags in GRADO_MAXIMO_TAGS.items():
        for tag in tags:
            if tag in grado_norm:
                return code
    print(f"Warning: '{grado}' not recognized as grado_maximo.")
    return None


def clean_email(email):
    """
    Clean and validate email address.
    """
    email = email.strip().lower()
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(email_pattern, email):
        return email
    else:
        print(f"Warning: '{email}' is not a valid email address.")
        return None


# cleaning functions for grados
def clean_degree_type(tipo):
    """
    Map the input string (label/tag) to the GradoTipo code (Lic,Msc,Phd). If no match is found, return GradoTipo.UNKNOWN.
    """
    tipo_normalized = tipo.strip().lower().replace(" ", "").replace(".", "").replace(",", "")
    for code, tag_list in SanitizeGradoForm.get_type_tags().items():
        for tag in tag_list:
            if tipo_normalized == tag.lower():
                return code

    print(f"Warning: '{tipo}' not found in GradoTipo TAGS.Default to unknown")
    return GradoTipo.UNKNOWN


def clean_degree_name(name):
    """
    Clean the degree name: capitalize and normalize whitespaces
    """
    return string.capwords(name)


def clean_creation_date(fecha):
    """
    Clean the creation date: accept YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or just YYYY (as YYYY-01-01).
    Returns a datetime.date or None.
    """
    if not fecha:
        return None
    fecha = str(fecha).strip()
    # Try full date formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(fecha, fmt).date()
        except ValueError:
            continue
    # Try year only
    if fecha.isdigit() and len(fecha) == 4:
        return datetime.strptime(fecha + "-01-01", "%Y-%m-%d").date()
    print(f"Warning: '{fecha}' is not a recognized date format.")
    return None


def clean_orcid_id(orcid):
    """
    Clean the ORCID ID to ensure it follows the standard format: "0000-0000-0000-0000".
    """
    if not orcid:
        return None

    # Extract ORCID ID using regex
    orcid_pattern = r"\b\d{4}-\d{4}-\d{4}-\d{4}\b"
    match = re.search(orcid_pattern, orcid)

    if match:
        return match.group()  # Return the valid ORCID ID
    else:
        print(f"Warning: '{orcid}' is not a valid ORCID ID.")
        return None


# cleaning for institutions
def clean_sigla(sigla):
    """
    Clean the "sigla" field to ensure it's uppercase and without extra spaces.
    """
    return sigla.strip().upper()


# common
def clean_pais(pais):
    """
    Clean the "pais" field to ensure it's a valid ISO country code.
    """
    SPANISH_TO_ENGLISH = {
        "Estados Unidos": "United States",
        "Canadá": "Canada",
        "México": "Mexico",
        "Perú": "Peru",
        "Brasil": "Brazil",
        "Panamá": "Panama",
        "República Dominicana": "Dominican Republic",
        "Jamaica": "Jamaica",
        "Trinidad y Tobago": "Trinidad and Tobago",
        "Surinam": "Suriname",
        "Belice": "Belize",
        "San Vicente y las Granadinas": "Saint Vincent and the Grenadines",
        "Santa Lucía": "Saint Lucia",
        "Granada": "Grenada",
        "San Cristóbal y Nieves": "Saint Kitts and Nevis",
        "España": "Spain",
        "Italia": "Italy",
    }
    pais = pais.split(",")[-1] if len(pais.split(",")) > 1 else pais
    if countries.by_name(pais.strip().title()):
        return pais.strip().title()
    elif pais.strip().title() in SPANISH_TO_ENGLISH:
        eng_name = SPANISH_TO_ENGLISH[pais.strip().title()]
        if countries.by_name(eng_name):
            return eng_name
        else:
            print(f"Warning: '{pais.strip().title()}' mapped to '{eng_name}', but not found in countries list. Default to None")
            return None
    else:
        print(f"Warning: '{pais}' not found in countries list. Default to None")
        return None
