from django.conf import settings
from django.db import models


class CorruptedType(models.TextChoices):
    INVALID_UNIVERSITY = "invalid_university", "Corrupted University"


class CorruptedAcademicoEntry(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200, null=True, blank=True)
    universidad = models.CharField(max_length=200, blank=True)
    pais_universidad = models.CharField(max_length=100, blank=True, null=True)
    webpage = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    grado_maximo = models.CharField(max_length=20, default=None, blank=True, null=True)
    # history data
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    is_deleted = models.BooleanField(default=False)
    invalid_type = models.CharField(max_length=50, choices=CorruptedType.choices, help_text="Type of invalid entry")


class CorruptedGradoEntry(models.Model):
    nombre = models.CharField(max_length=200)
    nombre_es = models.CharField(max_length=200, null=True, blank=True)
    web_site = models.URLField(blank=True, null=True)
    tipo = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    universidad = models.CharField(max_length=200, blank=True, null=True)
    pais_universidad = models.CharField(max_length=100, blank=True, null=True)
    unidad = models.CharField(max_length=200, blank=True, null=True)
    fecha_creacion = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=False, null=True)
    invalid_type = models.CharField(max_length=50, choices=CorruptedType.choices, help_text="Type of invalid entry")

    # history data
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    is_deleted = models.BooleanField(default=False)
