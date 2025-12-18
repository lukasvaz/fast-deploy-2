from django.urls import path

from . import views

app_name = "api"
urlpatterns = [
    path("buscar/academico/", views.AcademicoSearchBasicView.as_view(), name="academico_search_basic"),
    path("buscar/academico/avanzada/", views.AcademicoSearchAdvancedView.as_view(), name="academico_search_advanced"),
    path("buscar/institucion/", views.InstitucionSearchView.as_view(), name="institucion_search"),
    path("buscar/programa/", views.GradoSearchView.as_view(), name="grado_search"),
    path("buscar/programa/avanzada/", views.GradoSearchAdvancedView.as_view(), name="grado_search_advanced"),
    path("academico/", views.AcademicoGetIdView.as_view(), name="academico_get_id"),
    path("institucion/", views.InstitucionGetIdView.as_view(), name="institucion_get_id"),
    path("areas/", views.AreasListView.as_view(), name="areas_all"),
    path("subareas/", views.SubareasByAreaView.as_view(), name="subareas_by_area"),
    path("programa/", views.GradoGetIdView.as_view(), name="grado_get_id"),
]
