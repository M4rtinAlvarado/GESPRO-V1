from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from proyectos.models import Proyecto, Actividad, ActividadDifusion, ActividadBase, LineaTrabajo, ActividadDifusion_Linea, Actividad_Encargado, Fecha
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import models
from .gantt import calcular_gantt_data



def obtener_datos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto
    ).order_by('fecha_creacion')
    
    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto
    ).order_by('fecha_creacion')
    
    todas_actividades = []

    # Actividades normales
    for actividad in actividades_normales:
        fechas_lista = []
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "id": actividad.id,
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })


        consulta_2 = Actividad_Encargado.objects.filter(actividad=actividad).select_related('encargado')
        encargados = [
            {
                "id": rel.encargado.id,
                "nombre": rel.encargado.nombre, 
                "correo": rel.encargado.correo_electronico
            } 
            for rel in consulta_2
]

        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Normal',
            'encargados': encargados,
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'estado_valor': actividad.estado, 
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
        })

    # Actividades de difusión
    for actividad in actividades_difusion:
        fechas_lista = []
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "id": actividad.id,
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })

        consulta= ActividadDifusion_Linea.objects.filter(actividad=actividad).select_related('linea_trabajo')
        lineas_trabajo = [rel.linea_trabajo.nombre for rel in consulta]

        consulta_2 = Actividad_Encargado.objects.filter(actividad=actividad).select_related('encargado')
        encargados = [
            {
                "id": rel.encargado.id,
                "nombre": rel.encargado.nombre, 
                "correo": rel.encargado.correo_electronico
            } 
            for rel in consulta_2
        ]



        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Difusión',
            'encargados': encargados,
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'estado_valor': actividad.estado, 
            'linea_trabajo': lineas_trabajo,
        })

    estados = [
        ('PEN', 'Pendiente'),
        ('LPC', 'Listo para comenzar'),
        ('EPR', 'En progreso'),
        ('COM', 'Completada'),
        ('TER', 'Terminada'),
    ]

    context = {
        'proyecto': proyecto,
        'actividades': todas_actividades,
        'estados': estados,
    }

    return context



def vista_gantt(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Obtener todas las actividades normales (a través de linea_trabajo) ordenadas por ID de línea de trabajo
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto
    ).select_related('linea_trabajo').order_by('linea_trabajo__id', 'fecha_creacion')
    
    # Obtener todas las actividades de difusión (directamente relacionadas con proyecto)
    actividades_difusion = ActividadDifusion.objects.filter(proyecto=proyecto).order_by('fecha_creacion')
    
    # Combinar todas las actividades en una lista
    todas_actividades = []

    for actividad in actividades_normales:
        fechas = actividad.fechas.filter(estado=True)
        
        fechas_lista = []
        for fecha in fechas:
            fechas_lista.append({
                "fecha_inicio": fecha.fecha_inicio.strftime('%Y-%m-%d') if fecha.fecha_inicio else None,
                "fecha_fin": fecha.fecha_fin.strftime('%Y-%m-%d') if fecha.fecha_fin else None
            })
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            "fechas": fechas_lista,
            'tipo': 'Normal',
            'estado': actividad.estado,
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
            'linea_trabajo_id': actividad.linea_trabajo.id if actividad.linea_trabajo else 999999,  # ID para ordenamiento
            'orden_tipo': 1,  # Prioridad para ordenamiento (Normal = 1)
        })
    
    for actividad in actividades_difusion:
        fechas = actividad.fechas.filter(estado=True)
        
        fechas_lista = []
        for fecha in fechas:
            fechas_lista.append({
                "fecha_inicio": fecha.fecha_inicio.strftime('%Y-%m-%d') if fecha.fecha_inicio else None,
                "fecha_fin": fecha.fecha_fin.strftime('%Y-%m-%d') if fecha.fecha_fin else None
            })
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Difusión',
            'estado': actividad.estado,
            'linea_trabajo': 'Difusión',  # Grupo para actividades de difusión
            'linea_trabajo_id': 1000000,  # ID alto para que aparezca al final
            'orden_tipo': 2,  # Prioridad para ordenamiento (Difusión = 2)
        })

    # Ordenar actividades por: 1) Tipo (Normal primero, Difusión después), 2) ID de línea de trabajo, 3) Fecha de inicio
    todas_actividades.sort(key=lambda x: (
        x['orden_tipo'],  # 1 para Normal, 2 para Difusión
        x['linea_trabajo_id'],  # ID de línea de trabajo numéricamente
        x['fechas'][0]['fecha_inicio'] if x['fechas'] and x['fechas'][0]['fecha_inicio'] else '9999-12-31'
    ))
    
    # Agregar información sobre separadores de grupo
    linea_trabajo_anterior = None
    for i, actividad in enumerate(todas_actividades):
        # Mostrar separador si es la primera actividad o si cambia la línea de trabajo
        actividad['mostrar_separador'] = (i == 0 or actividad['linea_trabajo'] != linea_trabajo_anterior)
        linea_trabajo_anterior = actividad['linea_trabajo']

    # Calcular columnas semanales y posiciones
    gantt_data = calcular_gantt_data(todas_actividades)
    
    context = {
        'proyecto': proyecto,
        'total_actividades': todas_actividades,
        'gantt_data': gantt_data,
    }

    return render(request, 'vistas/vista_gantt.html', context)



def lista_actividades(request, proyecto_id):
    
    context = obtener_datos(request, proyecto_id)

    return render(request, "vistas/vista_lista.html", context)


def vista_tablero(request, proyecto_id):

    context = obtener_datos(request, proyecto_id)

    return render(request, 'vistas/vista_tablero.html', context)



@csrf_exempt
def actualizar_estado(request):
    if request.method == 'POST':
        actividad_id = request.POST.get('actividad_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        try:
            actividad = ActividadBase.objects.get(id=actividad_id)
            actividad.estado = nuevo_estado
            actividad.save()
            return JsonResponse({'success': True})
        except ActividadBase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Actividad no encontrada'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})        

def editar_actividad(request, actividad_id):
    actividad = get_object_or_404(ActividadBase, id=actividad_id)  # Base permite normal o difusión
    
    if request.method == 'POST':
        nuevo_nombre = request.POST.get('nombre')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        # Actualizar nombre si se envió
        if nuevo_nombre:
            actividad.nombre = nuevo_nombre
            actividad.save()

        # Actualizar o crear registro de fechas
        if fecha_inicio and fecha_fin:
            fecha_obj, created = Fecha.objects.get_or_create(
                actividad=actividad,
                estado=True,  # solo una fecha activa
                defaults={'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}
            )
            if not created:
                fecha_obj.fecha_inicio = fecha_inicio
                fecha_obj.fecha_fin = fecha_fin
                fecha_obj.save()

        messages.success(request, f'Actividad "{actividad.nombre}" actualizada correctamente.')

        # Si la actividad es de difusión o normal, redirige según tipo
        if hasattr(actividad, 'proyecto'):  # difusión
            return redirect('vista_tablero', proyecto_id=actividad.proyecto.id)
        elif hasattr(actividad, 'linea_trabajo'):  # normal
            return redirect('vista_tablero', proyecto_id=actividad.linea_trabajo.proyecto.id)

    return redirect('vista_tablero', proyecto_id=actividad.id) 



def editar_encargado(request):
    # Por ahora no hace nada, solo devuelve un redirect temporal
    return redirect('lista_actividades', proyecto_id=1)

def eliminar_encargado(request):
    # TODO: Implementar la eliminación
    return redirect(request.META.get('HTTP_REFERER', '/'))
