from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha Modificación")

    @classmethod
    def verbose_name(cls):
        return cls._meta.verbose_name.title()
