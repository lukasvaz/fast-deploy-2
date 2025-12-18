from modeltranslation.translator import TranslationOptions, translator

from .models import GradoInstancia


class GradoInstanciaTranslationOptions(TranslationOptions):
    fields = ("nombre",)


translator.register(GradoInstancia, GradoInstanciaTranslationOptions)
