from django.shortcuts import render, get_object_or_404
from proyectos.models import Proyecto, Actividad, ActividadDifusion
from django.db.models import Prefetch
from django.http import JsonResponse
import json


# Create your views here.


def listado_alertas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto,
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        'alertas',
        'fechas'
    ).distinct()

    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto,
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        'alertas',
        'fechas'
    ).distinct()


    actividades = list(actividades_normales) + list(actividades_difusion)

    for actividad in actividades:
        fecha_activa = actividad.fechas.filter(estado=True).order_by('-fecha_fin').first()
        actividad.fecha_limite = fecha_activa.fecha_fin if fecha_activa else None
        actividad.fecha_inicio = fecha_activa.fecha_inicio if fecha_activa else None
        # Contar alertas pendientes (no enviadas)
        actividad.alertas_pendientes_count = actividad.alertas.filter(enviado=False).count()

    return render(request, "alertas/listado_alertas.html", {
        "proyecto": proyecto,
        "actividades": actividades
    })
def modificar_alerta(request):
    #recibe una lista de ids de laertas que modificar, recibe los campos con sus nuevos valores fecha_creacion, fecha_envio
    if request.method == "POST":
        ids = request.POST.getlist("ids[]")
        fecha_creacion = request.POST.get("fecha_creacion")
        fecha_envio = request.POST.get("fecha_envio")
        enviado = request.POST.get("enviado")
        from proyectos.models import Alerta
        alertas = Alerta.objects.filter(id__in=ids)

        for alerta in alertas:
            if fecha_creacion:
                alerta.fecha_creacion = fecha_creacion
            if fecha_envio:
                alerta.fecha_envio = fecha_envio
            alerta.save()

        return redirect('listado_alertas', proyecto_id=alertas.first().actividad.linea_trabajo.proyecto.id)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

def crear_alertas(request):
    print("Crear alertas")
    data = json.loads(request.body)
    print("Datos recibidos:", data)
    return JsonResponse({"status": "success"})

def mover_alertas(request):
    print("Modificar alertas")
    data = json.loads(request.body)
    print("Datos recibidos:", data)
    return JsonResponse({"status": "success"})
def eliminar_alertas(request):
    print("Eliminar alertas")
    data = json.loads(request.body)
    print("Datos recibidos:", data)
    return JsonResponse({"status": "success"})