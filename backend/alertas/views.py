from django.shortcuts import render, get_object_or_404, redirect
from proyectos.models import *
from django.db.models import Prefetch
from django.http import JsonResponse
import json
from datetime import datetime
from django.utils import timezone
import pytz

# Zona horaria de Chile
CHILE_TZ = pytz.timezone('America/Santiago')


# Create your views here.


def listado_alertas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # 1. Prefetch de Alertas (dentro de Periodo)
    # Filtramos alertas activas
    alertas_prefetch = Prefetch(
        'alertas',
        queryset=Alerta.objects.filter(activo=True).order_by('fecha_envio')
    )

    # 2. Prefetch de Periodos (dentro de Actividad)
    # Usamos related_name='fechas' según tu modelo Periodo
    periodos_prefetch = Prefetch(
        'fechas',
        queryset=Periodo.objects.filter(activo=True).prefetch_related(alertas_prefetch).order_by('fecha_inicio')
    )

    # 3. Consultas de Actividades
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto,
        activo=True # Usamos activo en lugar de estado
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        periodos_prefetch
    ).distinct()

    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto,
        activo=True
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        periodos_prefetch
    ).distinct()

    actividades = list(actividades_normales) + list(actividades_difusion)

    # 4. Procesamiento de datos para la vista (Resumen en la fila padre)
    for actividad in actividades:
        # Obtenemos los periodos ya pre-cargados
        periodos = list(actividad.fechas.all())
        
        if periodos:
            actividad.fecha_inicio_resumen = periodos[0].fecha_inicio
            actividad.fecha_fin_resumen = periodos[-1].fecha_fin
            
            # Contar alertas pendientes en todos los periodos
            total_pendientes = 0
            for p in periodos:
                total_pendientes += len([a for a in p.alertas.all() if not a.enviado])
            actividad.alertas_pendientes_count = total_pendientes
        else:
            actividad.fecha_inicio_resumen = None
            actividad.fecha_fin_resumen = None
            actividad.alertas_pendientes_count = 0

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

        # Fix redirect logic for new schema
        first_alerta = alertas.first()
        if first_alerta:
            periodo = first_alerta.periodo
            actividad_base = periodo.actividad
            
            proyecto_id = None
            # Try to find project id
            try:
                # Try Actividad (Normal)
                actividad = Actividad.objects.get(id=actividad_base.id)
                proyecto_id = actividad.linea_trabajo.proyecto.id
            except Actividad.DoesNotExist:
                try:
                    # Try ActividadDifusion
                    actividad_dif = ActividadDifusion.objects.get(id=actividad_base.id)
                    proyecto_id = actividad_dif.proyecto.id
                except ActividadDifusion.DoesNotExist:
                    pass
            
            if proyecto_id:
                return redirect('listado_alertas', proyecto_id=proyecto_id)
        
        return JsonResponse({"status": "error", "message": "No se pudo determinar el proyecto para redireccionar"}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

def crear_alertas(request):
    if request.method == "POST":
        try:
            datos = json.loads(request.body)
            
            if isinstance(datos, dict):
                    datos = [datos]

            ahora = timezone.now()
            
            for item in datos:
                # CAMBIO: Ahora recibimos 'periodo_id', no 'actividad'
                periodo_id = item.get("periodo_id") 
                fecha_envio_str = item.get("fecha")
                
                if not periodo_id:
                    continue

                # Parsear la fecha como naive
                fecha_envio_dt = datetime.strptime(fecha_envio_str, "%Y-%m-%d %H:%M:%S")
                # Localizarla a Chile (la fecha viene en hora local de Chile)
                fecha_envio_aware = CHILE_TZ.localize(fecha_envio_dt)

                if fecha_envio_aware > ahora:
                    # Buscamos el Periodo
                    periodo = get_object_or_404(Periodo, id=periodo_id)
                    
                    Alerta.objects.create(
                        periodo=periodo, # Relación con Periodo
                        fecha_envio=fecha_envio_aware,
                        enviado=False,
                        activo=True
                    )
                else:
                    print(f"La fecha: {fecha_envio_aware} ya pasó")
                    
            return JsonResponse({"success": True, "mensaje": "Alertas creadas correctamente"})
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
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
                    
                    # Parsear la fecha como naive
                    fecha_envio_dt = datetime.strptime(fecha_envio_str, "%Y-%m-%d %H:%M:%S")
                    # Localizarla a Chile (la fecha viene en hora local de Chile)
                    fecha_envio_aware = CHILE_TZ.localize(fecha_envio_dt)
                    
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
                alerta.activo = False # CAMBIO: estado -> activo
                alerta.save()
                
            return JsonResponse({"success": True, "mensaje": "Alertas eliminadas correctamente"})
            
        except Exception as e:
            return JsonResponse({"success": False, "mensaje": f"Error: {str(e)}"})

    return JsonResponse({"success": False, "mensaje": "Método no permitido"}, status=405)