import re

import bs4
import httpx
from django.core.management.base import BaseCommand

from grados.forms import SanitizeGradoForm
from grados.models import GradoInstancia, ValidationStates


def validate_grado_url_field(grado_ob):
    """
    Validate the grado URL in the specified field by checking its accessibility and extracting key HTML tags.
    Args:
    - grado_ob: GradoInstancia object containing the URL to validate and the degree type.
    Returns:
    - errors: list of error messages (
            - if URL  throws code different than 200
            - Generic academic degree name is not present in the HTML tags)
    - suggested_value: suggested correction for name_es
    """

    def filter_tags(text_list, tipo):
        """
        Returns a list of tags from text_list that match the given degree tipo.
        """
        # regex  omiting especial chars
        filtered_results = []
        tags_to_search = SanitizeGradoForm.get_type_tags().get(tipo, [])
        for list_item in text_list:
            for field_tag in tags_to_search:
                # stopwords_pattern = r"({})$".format("|".join([r"/", r"-", r"\|", r"\(", r"\)"]))
                pattern = r"^{} ".format(re.escape(field_tag))
                # exact match  with tipo keyword
                if re.search(pattern, list_item, re.IGNORECASE):
                    filtered_results.append(list_item)
                    break
        # transform to pascalcase and remove extra spaces
        filtered_results = [entry.title().strip() for entry in filtered_results]
        # remove duplicates
        filtered_results = list(set(filtered_results))
        # omit  large text list (probably listing many degrees)
        if len(filtered_results) > 10:
            return []
        return filtered_results

    tipo = grado_ob.tipo
    url = grado_ob.web_site
    errors = []
    extracted_entries = []
    matched_tags = []
    suggested_value = None

    if not url:
        errors.append("La URL está vacía")
        return errors, suggested_value
    try:
        with httpx.Client(timeout=10, headers={"User-Agent": "Mozilla/5.0"}, verify=False) as client:
            response = client.get(url, follow_redirects=True)
            if response.status_code != 200:
                errors.append(f"La URL respondió con el estado {response.status_code}")
            else:
                soup = bs4.BeautifulSoup(response.text, "html.parser")
                # get tags lists
                # extracted_tags["title"] = [soup.title.string] if soup.title else []
                for tag in ["h1", "h2", "h3", "b", "strong"]:
                    extracted_entries.extend([element.get_text(strip=True) for element in soup.find_all(tag)])
                    if soup.title.string:
                        extracted_entries.append(soup.title.string)
                # filter tags by grado tipo
                matched_tags = filter_tags(extracted_entries, tipo)
                if matched_tags:
                    suggested_value = matched_tags[0]
                else:
                    errors.append("No se encontraron coincidencias relevantes en la página web")

    except Exception as e:
        errors.append(f"Error al consultar la URL: {str(e)}")
    return errors, suggested_value


class Command(BaseCommand):
    help = "Validates the web_site URL for each GradoInstancia"

    def handle(self, *args, **kwargs):
        failed = 0
        success = 0
        suggestion = 0

        grados = GradoInstancia.objects.filter(verification_state=ValidationStates.PENDING)
        for grado in grados:
            try:
                url = grado.web_site
                error, suggested_value = validate_grado_url_field(grado)
                if error:
                    grado.verification_state = ValidationStates.INVALID_URL
                    grado.save()
                    failed += 1
                if not error:
                    grado.verification_state = ValidationStates.VALID
                    grado.save()
                    success += 1
                    self.stdout.write(self.style.SUCCESS(f"{grado} → URL OK: {url}"))
                if suggested_value:
                    if not grado.nombre_es:
                        grado.nombre_es = suggested_value
                        grado.save()
                    suggestion += 1
                    self.stdout.write(self.style.SUCCESS(f"  Suggested nombre_es: {suggested_value}"))
            except Exception:
                failed += 1
                grado.verification_state = ValidationStates.INVALID_URL
                grado.save()
                self.stdout.write(self.style.ERROR(f"{grado} → Invalid URL: {url}"))

        self.stdout.write(self.style.SUCCESS(f"✓ Validation completed: {success} valid, {failed} invalid, {suggestion} suggestions."))
