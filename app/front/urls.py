from django.urls import path

from . import views

app_name = "front"
urlpatterns = [
    path("", views.index, name="index"),
    path("buscar/", views.buscar, name="buscar"),
    path("indicadores/", views.indicadores, name="indicadores"),
    path("compute_indicadores/", views.compute_indicadores, name="compute_indicadores"),
    path("institucion/", views.instituciones, name="instituciones"),
    path("institucion/<int:id_institucion>/", views.institucion, name="institucion"),
    path("uni/carga/<int:id_universidad>/", views.carga_masiva, name="carga_masiva"),
    path("academico/<int:id_academico>/", views.academico, name="academico"),
    path("academico/edit/<int:id_academico>/", views.academico_edit, name="academico_edit"),
    path("grado/<int:id_grado>/", views.grado, name="grado"),
    path("universidad_link_new/", views.universidad_link_new, name="universidad_link_new"),
    path("universidad_link_delete/", views.universidad_link_delete, name="universidad_link_delete"),
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuario_invitacion/", views.usuario_invitacion, name="usuario_invitacion"),
    path("usuario_delete", views.usuario_delete, name="usuario_delete"),
    path("areas", views.areas, name="areas"),
    path("api", views.api, name="api"),
    path("usuario_invitacion_academico", views.usuario_invitacion_academico, name="usuario_invitacion_academico"),
    path("carga_automatica", views.carga_automatica, name="carga_automatica"),
]
