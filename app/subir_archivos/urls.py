from django.urls import path

from . import views

app_name = "subir_archivos"

urlpatterns = [
    path("sanitizar_data_grado", views.sanitizar_data_grados, name="sanitizar_data_grado"),
    path("load_data_grados", views.load_data_grados, name="load_data"),
    path("sanitizar_data_academico", views.sanitizar_data_academico, name="sanitizar_data_academico"),
    path("load_data_academicos", views.load_data_academicos, name="load_data_academicos"),
    path("sanitizar_data_instituciones", views.sanitizar_data_instituciones, name="sanitizar_data_instituciones"),
    path("load_data_instituciones", views.load_data_instituciones, name="load_data_instituciones"),
]
