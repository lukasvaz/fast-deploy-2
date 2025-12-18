from modeltranslation.translator import TranslationOptions, translator

from .models import Area, Dominio, Subarea


class AreaTranslationOptions(TranslationOptions):
    fields = (
        "nombre",
        "descripcion",
    )


class SubareaTranslationOptions(TranslationOptions):
    fields = (
        "nombre",
        "descripcion",
    )


class DominioTranslationOptions(TranslationOptions):
    fields = ("nombre",)


translator.register(Area, AreaTranslationOptions)
translator.register(Subarea, SubareaTranslationOptions)
translator.register(Dominio, DominioTranslationOptions)
