from django.contrib.postgres.search import TrigramSimilarity
from django.db import models
from django.db.models.functions import Greatest

from universidad.models import Unidad


class GradoTipo(models.TextChoices):
    TECHNICIAN = "TECH", "Técnico Superior"
    LICENCIATURA = "LIC", "Licenciatura"
    MAESTRIA = "MSC", "Magister"
    DOCTORADO = "PHD", "Doctorado"
    UNKNOWN = "UNK", "Desconocido"
    # @classmethod
    # def get_field_tags(cls):
    #     """
    #     Output contract:
    #         - Output:
    #             - dict: A dictionary mapping each field to its associated tags.You should access the tags using the field name as the key
    #             (ie get_field_tags()[GradoTipo.Licenciatura]).
    #     """
    #     '''
    #     Returns a list of tags associated with the given field.

    #     '''
    #     return {
    #         "TECH": ["Técnico Superior","Technician","Technical"],
    #         "LIC": ["Licenciatura","Lic","Undergraduate"],
    #         "MSC": ["Maestría", "Master","Maestria","Magister","Msc"],
    #         "PHD": ["Doctorado","Doctorate","Phd"]
    #     }


class ValidationStates(models.TextChoices):
    VALID = "VALID", "Válido"
    INVALID_URL = "INVALID_URL", "Inválido"
    PENDING = "PENDING", "Pendiente"


class GradoInstancia(models.Model):
    class Meta:
        unique_together = ("nombre", "tipo", "unidad")

    nombre = models.CharField(max_length=300)  # nombre_en and nombre_es will be created by modeltranslation
    tipo = models.CharField(max_length=30, choices=GradoTipo.choices)
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, null=True)
    fecha_creacion = models.DateField(null=True)
    web_site = models.URLField(max_length=500, null=True)
    activo = models.BooleanField(null=True)
    is_deleted = models.BooleanField(default=False)
    verification_state = models.CharField(max_length=20, choices=ValidationStates.choices, default=ValidationStates.PENDING)

    class GradoInstanciaManager(models.Manager):
        class GradoInstanciaQuerySet(models.QuerySet):
            def order_by_priority(self, query=None):
                """
                Orders the queryset by priority based on the query.
                Priority order:
                    0. similarity if query
                    1. Verified first
                """
                qs = self.annotate(
                    verificated=models.Case(
                        models.When(verification_state=ValidationStates.VALID, then=1),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                )

                order_fields = ["-verificated"]
                if query:
                    similarity_cases = [
                        Greatest(
                            TrigramSimilarity("nombre_en", query_item),
                            TrigramSimilarity("nombre_es", query_item),
                        )
                        for query_item in query
                    ]
                    similarity_cases.append(models.Value(0.0))
                    qs = qs.annotate(similarity=Greatest(*similarity_cases))
                    order_fields = ["-similarity"] + order_fields
                return qs.order_by(*order_fields)

        def get_queryset(self):
            return self.GradoInstanciaQuerySet(self.model, using=self._db)

        def get_or_create(self, nombre, unidad, **kwargs):
            # Search by  names in any unidad  for universidad
            unidades_ids = unidad.universidad.unidades_set.values_list("id", flat=True)
            programs = self.filter(unidad__id__in=unidades_ids)
            for program in programs:
                if program.get_name_normalized() == GradoInstancia(nombre=nombre, unidad=unidad).get_name_normalized():
                    return program, False

            # If not found, create new
            return super().get_or_create(nombre=nombre, unidad=unidad, **kwargs)

    objects = GradoInstanciaManager()

    def __str__(self):
        return f"{self.nombre} ({self.unidad})"

    def get_name_normalized(self):
        replacements = [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")]
        omissions = ["-", "_", ",", ".", "'", "`"]
        for old, new in replacements:
            text = self.nombre.replace(old, new)
        for char in omissions:
            text = text.replace(char, "")
        return " ".join(text.split()).lower()

    @property
    def is_verification_pending(self):
        return self.verification_state == ValidationStates.PENDING

    @property
    def is_verified(self):
        return self.verification_state == ValidationStates.VALID

    @property
    def is_unverified(self):
        return self.verification_state == ValidationStates.INVALID_URL

    def get_verification_error(self):
        if self.is_unverified and self.verification_state == ValidationStates.INVALID_URL:
            return ValidationStates.INVALID_URL


# class GradoInstanciaQuerySet(models.QuerySet):
#     def active(self):
#         return self.filter(activo=True, is_deleted=False)

#     def pending_verification(self):
#         return self.filter(verification_state=ValidationStates.PENDING)

#     def verified(self):
#         return self.filter(verification_state=ValidationStates.VALID)

#     def unverified(self):
#         return self.filter(verification_state=ValidationStates.INVALID_URL)

# class GradoInstanciaManager(models.Manager):
#     def get_queryset(self):
#         return GradoInstanciaQuerySet(self.model, using=self._db)

#     def active(self):
#         return self.get_queryset().active()

#     def pending_verification(self):
#         return self.get_queryset().pending_verification()

#     def verified(self):
#         return self.get_queryset().verified()

#     def unverified(self):
#         return self.get_queryset().unverified()
