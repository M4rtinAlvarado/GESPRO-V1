from django.urls import path
from . import views


urlpatterns = [
    path('vista_gantt/<int:proyecto_id>/', views.vista_gantt, name='vista_gantt'),
    path('lista_actividades/<int:proyecto_id>/', views.lista_actividades, name="lista_actividades"),
    path('vista_tablero/<int:proyecto_id>/', views.vista_tablero, name='vista_tablero'),
    #path("actualizar_estado/<int:actividad_id>/", views.actualizar_estado_actividad, name="actualizar_estado_actividad"),
    path("actualizar_estado/", views.actualizar_estado, name="actualizar_estado"),
    path('editar_actividad/', views.editar_actividad, name='editar_actividad'),
    path('historial/<int:actividad_id>/', views.obtener_historial, name='obtener_historial'),
    path('crear_actividad/', views.crear_actividad, name='crear_actividad'),


    path("reportes/<int:proyecto_id>/", views.reportes, name="reportes"),
]