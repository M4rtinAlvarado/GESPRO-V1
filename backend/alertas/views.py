from django.shortcuts import render, get_object_or_404
from proyectos.models import *
from django.db.models import Prefetch
from django.http import JsonResponse
import json
from datetime import datetime
from django.utils import timezone


# Create your views here.


def listado_alertas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    alertas_filtradas = Prefetch(
        'alertas', 
        queryset=Alerta.objects.filter(estado=True)
    )

    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto, 
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        alertas_filtradas,
        'fechas'
    ).distinct()

    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto,
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        alertas_filtradas,
        'fechas'
    ).distinct()


    actividades = list(actividades_normales) + list(actividades_difusion)

    for actividad in actividades:
        fechas_activas = actividad.fechas.filter(estado=True)
        
        # Obtener la primera fecha de inicio (la más temprana)
        fecha_inicio_obj = fechas_activas.order_by('fecha_inicio').first()
        actividad.fecha_inicio = fecha_inicio_obj.fecha_inicio if fecha_inicio_obj else None
        
        # Obtener la última fecha de fin (la más tardía)
        fecha_fin_obj = fechas_activas.order_by('-fecha_fin').first()
        actividad.fecha_limite = fecha_fin_obj.fecha_fin if fecha_fin_obj else None
        
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
    if request.method == "POST":
        try:
            datos = json.loads(request.body)
            print("Datos recibidos:", datos)
            
            if isinstance(datos, dict):
                    datos = [datos]

            timezone.activate('America/Santiago')

            # 2. 💡 'localtime()' ahora usará la zona activada ('America/Santiago')
            ahora = timezone.localtime()
            
            # --- Proceso de Alertas ---
            for item in datos:
                print("creando alerta para: ", item)
                actividad_id = item.get("actividad")
                fecha_envio_str = item.get("fecha")
                


                fecha_envio_dt = datetime.strptime(fecha_envio_str, "%Y-%m-%d %H:%M:%S").replace(microsecond=0)
                    
                fecha_envio_aware = timezone.make_aware(fecha_envio_dt)

                if fecha_envio_aware > ahora:
                    actividad = get_object_or_404(ActividadBase, id=actividad_id)
                    
                    Alerta.objects.create(
                        actividad=actividad, 
                        fecha_envio=fecha_envio_aware,
                        enviado=False, 
                    )
                    print(f"Alerta creada para Actividad ID {actividad_id}")
                else:
                    print(ahora)
                    print(f"La fecha: {fecha_envio_aware} ya pasó, no se creo la alerta")
                    
            return JsonResponse({"success": True, "mensaje": "Alertas creadas correctamente"})
        
        except Exception as e:
            # Captura y reporta errores como Actividad no encontrada, formato de fecha, etc.
            print(f"ERROR DURANTE LA CREACIÓN DE ALERTA: {type(e).__name__}: {str(e)}")
            return JsonResponse({"success": False, "mensaje": f"Error: {str(e)}"}, status=400)

def mover_alertas(request):
    """
    Recibe un JSON con el formato: 
    [{'actividad': '11', 'alertas': [{'id_alerta': '24', 'fecha': '2025-11-09 11:04:00'}, ...]}]
    y actualiza la fecha de envío de las alertas si la nueva fecha no ha pasado.
    """
    # El diccionario request y las importaciones están implícitas para un entorno Django
    if request.method == "POST":
        try:
            # En un entorno real, la línea de abajo podría fallar si request.body está vacío.
            datos = json.loads(request.body)
            ahora = timezone.now()

            for item in datos:
                # La clave 'actividad' no se usa en la lógica, pero se itera sobre ella.
                alertas = item.get("alertas", [])
                
                for alerta_item in alertas:
                    alerta_id = alerta_item.get("id_alerta")
                    fecha_envio_str = alerta_item.get("fecha")
                    
                    # 💡 CAMBIO CLAVE: Se añade '%S' para el componente de segundos.
                    fecha_envio_dt = datetime.strptime(fecha_envio_str, "%Y-%m-%d %H:%M:%S")
                    
                    # Es buena práctica asegurar que la datetime es 'aware' para la comparación con timezone.now()
                    fecha_envio_aware = timezone.make_aware(fecha_envio_dt)
                    
                    # verificar que la fecha no haya pasado
                    if fecha_envio_aware > ahora:
                        # Usar int(alerta_id) si el ID de Alerta es un campo numérico
                        alerta = get_object_or_404(Alerta, id=alerta_id)
                        alerta.fecha_envio = fecha_envio_aware
                        alerta.save()
                    else:
                        # Si estás en un entorno Django/producción, evita usar print(), 
                        # usa el logger de Python.
                        print(f"La fecha: {fecha_envio_aware} de la alerta {alerta_id} ya pasó, no se modificó.")
                        
            return JsonResponse({"success": True, "mensaje": "Alertas modificadas correctamente"})
            
        except Exception as e:
            # Captura de errores de formato JSON o errores de base de datos
            return JsonResponse({"success": False, "mensaje": f"Error: {str(e)}"})
    
    # Manejar otros métodos de request (GET, etc.)
    return JsonResponse({"success": False, "mensaje": "Método no permitido"}, status=405)

def eliminar_alertas(request):
    # Datos recibidos esperados: {'alertas_eliminar': ['24', '23']}
    if request.method == "POST":
        try:
            # Cargar el objeto JSON completo
            datos = json.loads(request.body)
            
            # 💡 CAMBIO CLAVE: Obtener la lista de IDs usando la clave 'alertas_eliminar'
            ids_a_eliminar = datos.get('alertas_eliminar', [])
            
            # Iterar sobre la lista de IDs
            for alerta_id in ids_a_eliminar:
                # Lógica original: buscar y marcar como inactivo
                alerta = get_object_or_404(Alerta, id=alerta_id)
                alerta.estado = False
                alerta.save()
                
            return JsonResponse({"success": True, "mensaje": "Alertas eliminadas correctamente"})
            
        except Exception as e:
            return JsonResponse({"success": False, "mensaje": f"Error: {str(e)}"})

    return JsonResponse({"success": False, "mensaje": "Método no permitido"}, status=405)