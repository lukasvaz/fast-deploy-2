from django.urls import path
from . import views
app_name = "revision"

urlpatterns = [
    path('interfaz_revision', views.interfaz_revision, name='interfaz_revision'),
    path('delete_corrupted_academico/', views.delete_corrupted_academico, name='delete_corrupted_academico'),
    path('delete_corrupted_grado/', views.delete_corrupted_grado, name='delete_corrupted_grado'),
    path('search_universidades/', views.search_universidades, name='search_universidades'),
    path('corrected_grado/', views.correct_grado, name='correct_grado'),
    path('correct_academico/', views.correct_academico, name='correct_academico'),
    path('bulk-delete/', views.bulk_delete_corrupted_entries, name='bulk_delete_corrupted_entries'),
    path('bulk-correct/', views.bulk_correct_entries, name='bulk_correct_entries'),
]
