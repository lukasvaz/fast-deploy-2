from django.urls import path

from . import views

app_name = "inst"
urlpatterns = [
    path("new/", views.institucion_new, name="institucion_new"),
    path("edit/", views.institucion_edit, name="institucion_edit"),
    path("delete/", views.institucion_delete, name="institucion_delete"),
    path("unidad_new/", views.unidad_new, name="unidad_new"),
    path("unidad_edit/", views.unidad_edit, name="unidad_edit"),
    path("unidad_delete/", views.unidad_delete, name="unidad_delete"),
    path("get_openalex_suggestions/", views.institucion_get_openalex_suggestions, name="get_openalex_suggestions"),
    path("get_ror_suggestions/", views.institucion_get_ror_suggestions, name="get_ror_suggestions"),
]
