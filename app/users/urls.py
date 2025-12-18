from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("registro/<uuid:invitation_code>", views.registro, name="registro"),
    path("registro_academico/<uuid:invitation_code>", views.registro_academico, name="registro_academico"),
]
