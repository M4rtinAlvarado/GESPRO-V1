from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from proyectos.models import *
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import models
from .gantt import calcular_gantt_data
import json
from django.urls import reverse 
from urllib.parse import urlencode, urlunparse



def obtener_datos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    all_encargados_qs = Encargado.objects.filter(estado=True)
    all_encargados = list(all_encargados_qs.values('id', 'nombre'))
    
    # SIN FILTRO DE ESTADO (como pediste)
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto
    ).order_by('fecha_creacion')
    
    # SIN FILTRO DE ESTADO (como pediste)
    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto
    ).order_by('fecha_creacion')
    
    todas_actividades = []

    # Actividades normales
    for actividad in actividades_normales:
        fechas_lista = []
        # Este filtro SÍ se aplica (correcto)
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "id": fecha.id,
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })

        # <-- CAMBIO AQUÍ: Filtramos solo encargados activos en esta relación
        consulta_2 = Actividad_Encargado.objects.filter(
            actividad=actividad, 
            estado=True  # <-- FILTRO AÑADIDO
        ).select_related('encargado')
        
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
        # Este filtro SÍ se aplica (correcto)
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "id": fecha.id,
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })

        consulta= ActividadDifusion_Linea.objects.filter(actividad=actividad).select_related('linea_trabajo')
        lineas_trabajo = [rel.linea_trabajo.nombre for rel in consulta]

        # <-- CAMBIO AQUÍ: Filtramos solo encargados activos en esta relación
        consulta_2 = Actividad_Encargado.objects.filter(
            actividad=actividad,
            estado=True  # <-- FILTRO AÑADIDO
        ).select_related('encargado')
        
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
        'all_encargados': all_encargados,
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




def editar_actividad(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("\n--- Datos recibidos en editar_actividad ---")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            print("------------------------------------------\n")

            actividad_id = data.get("id")
            nombre = data.get("nombre")
            encargados = data.get("encargados", [])
            periodos = data.get("periodos", [])

            print("------------------------------------------\n")
            #printar el encargado 0
            print(encargados[0]["nombre"])

            return JsonResponse({"success": True, "message": "Datos recibidos correctamente"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})
     




def enviar_correo_cambios(info_antes, info_despues):
    print("=== CAMBIOS EN ACTIVIDAD ===")
    print("Antes:", info_antes)
    print("Después:", info_despues)