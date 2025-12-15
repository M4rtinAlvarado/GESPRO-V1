from django.urls import path
from . import views


urlpatterns = [
    path('importar_proyecto/', views.importar_proyecto, name='importar_proyecto'),
    path('descargar_plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
    path('verificar_proyecto/', views.verificar_proyecto, name='verificar_proyecto'),
    path('exportar_gantt/<int:proyecto_id>/', views.exportar_proyecto_gantt, name='exportar_gantt'),
]   