from django.urls import path
from . import views


urlpatterns = [
    path('listado/<int:proyecto_id>/', views.listado_alertas,
    name='listado_alertas'),
    path('alertas/crear_alertas/', views.crear_alertas, name='crear_alertas'),
    path('alertas/modificar_alertas/', views.mover_alertas, name='modificar_alertas'),
    path('alertas/eliminar_alertas/', views.eliminar_alertas, name='eliminar_alertas'), 
]