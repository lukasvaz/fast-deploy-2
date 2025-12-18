from django.urls import path

from etl import views

app_name = "etl"
urlpatterns = [
    path("match_academic_web_to_dblp", views.match_academic_web_to_dblp, name="match_academic_web_to_dblp"),
    path("match_by_coauthor", views.match_by_coauthor, name="match_by_coauthor"),
    path("match_name_to_dblp", views.match_name_to_dblp, name="match_name_to_dblp"),
    path("save_academico", views.save_academico, name="save_academico"),
    path("carga_automatica_web", views.carga_automatica_web, name="carga_automatica_web"),  # Nueva ruta
]
