from django.urls import path

from . import views

app_name = "persona"
urlpatterns = [
    path("academico_new/", views.academico_new, name="academico_new"),
    path("academico_delete/", views.academico_delete, name="academico_delete"),
    path("academico_change_unidad/", views.academico_change_unidad, name="academico_change_unidad"),
    path("academico_update/<int:id_academico>/", views.academico_update, name="academico_update"),
    path("reload_academico/<int:id_academico>/", views.reload_academico, name="reload_academico"),
    path("reload_institucion/<int:id_institucion>/", views.reload_institucion, name="reload_institucion"),
    path("subarea_new/", views.subarea_new, name="subarea_new"),
    path("subarea_action/", views.subarea_action, name="subarea_action"),
    path("get_openalex_suggestion/", views.academico_get_openalex_suggestions, name="get_openalex_suggestions"),
    path("get_dblp_suggestion/", views.academico_get_dblp_suggestions, name="get_dblp_suggestions"),
]
