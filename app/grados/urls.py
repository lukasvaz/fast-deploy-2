from django.urls import path

from . import views

app_name = "grados"

urlpatterns = [
    path("grado_new/", views.grado_new, name="grado_new"),
    path("grado/edit/<int:id_grado>/", views.grado_edit, name="grado_edit"),
    path("grado_delete/", views.grado_delete, name="grado_delete"),
]
