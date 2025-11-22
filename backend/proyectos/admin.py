from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Proyecto)
admin.site.register(LineaTrabajo)
admin.site.register(ProductoAsociado)
admin.site.register(ActividadBase)
admin.site.register(Actividad)
admin.site.register(ActividadDifusion)
admin.site.register(Periodo)
admin.site.register(Alerta)
admin.site.register(Encargado)
admin.site.register(Actividad_Encargado)
admin.site.register(ActividadDifusion_Producto)
admin.site.register(ActividadDifusion_Linea)
#admin.site.register(ActividadDifusion_Encargado)






