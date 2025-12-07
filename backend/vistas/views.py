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
from vistas.alerta_cambios import registrar_y_notificar_cambios



def obtener_datos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    all_encargados_qs = Encargado.objects.filter(activo=True)
    all_encargados = list(all_encargados_qs.values('id', 'nombre', 'correo_electronico'))

    all_lineas_trabajo_qs = LineaTrabajo.objects.filter(activo=True, proyecto_id=proyecto_id)
    all_lineas_trabajo = list(all_lineas_trabajo_qs.values_list('nombre', flat=True)) 


    
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


        # <-- CAMBIO AQUÍ: Filtramos solo encargados activos en esta relación
        consulta_2 = Actividad_Encargado.objects.filter(
            actividad=actividad, 
            activo=True  # <-- FILTRO AÑADIDO
        ).select_related('encargado')
        
        encargados = [
            {
                "id": rel.encargado.id,
                "nombre": rel.encargado.nombre, 
                "correo": rel.encargado.correo_electronico
            } 
            for rel in consulta_2
        ]

        # obtenemos los periodos de la actividad, con su respectivo estado
        consulta_3 = Periodo.objects.filter(actividad=actividad).filter(activo=True)
        total_periodos = consulta_3.count()
        periodos = [
            {
                'id': periodo.id,
                'fecha_inicio': periodo.fecha_inicio,
                'fecha_fin': periodo.fecha_fin,
                'estado_valor': periodo.estado,  # <-- código almacenado en la BD (PEN, EPR, ...)
                'estado': periodo.get_estado_display() if hasattr(periodo, 'get_estado_display') else 'Sin estado',  # etiqueta para mostrar
                'indice': i + 1,
            }
            for i, periodo in enumerate(consulta_3)
        ]




        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            'tipo': 'Normal',
            'encargados': encargados,
            'periodos': periodos,
            'total_periodos': total_periodos,
            #'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            #'estado_valor': actividad.estado, 
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
        })

    # Actividades de difusión
    for actividad in actividades_difusion:

        consulta= ActividadDifusion_Linea.objects.filter(actividad=actividad).select_related('linea_trabajo')
        lineas_trabajo = [rel.linea_trabajo.nombre for rel in consulta]

        # <-- CAMBIO AQUÍ: Filtramos solo encargados activos en esta relación
        consulta_2 = Actividad_Encargado.objects.filter(
            actividad=actividad,
            activo=True  # <-- FILTRO AÑADIDO
        ).select_related('encargado')
        
        encargados = [
            {
                "id": rel.encargado.id,
                "nombre": rel.encargado.nombre, 
                "correo": rel.encargado.correo_electronico
            } 
            for rel in consulta_2
        ]

        # obtenemos los periodos de la actividad, con su respectivo estado
        consulta_3 = Periodo.objects.filter(actividad=actividad).filter(activo=True).order_by('fecha_inicio') 
        total_periodos = consulta_3.count()
        periodos = [
            {
                'id': periodo.id,
                'fecha_inicio': periodo.fecha_inicio,
                'fecha_fin': periodo.fecha_fin,
                'estado_valor': periodo.estado,  # <-- código almacenado en la BD (PEN, EPR, ...)
                'estado': periodo.get_estado_display() if hasattr(periodo, 'get_estado_display') else 'Sin estado',  # etiqueta para mostrar,
                'indice': i + 1,
            }
            for i, periodo in enumerate(consulta_3)
        ]
        
            

        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",

            'tipo': 'Difusión',
            'encargados': encargados,
            'periodos': periodos,
            'total_periodos': total_periodos,
            #'estado_valor': actividad.estado, 
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
        'all_lineas_trabajo': all_lineas_trabajo,
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



 

def actualizar_estado(request):
    periodo_id = request.POST.get('periodo_id')
    nuevo_estado = request.POST.get('nuevo_estado')

    if not (periodo_id and nuevo_estado):
        return JsonResponse({'success': False, 'error': 'Faltan parámetros'})

    try:
        periodo = Periodo.objects.get(id=periodo_id)
        # validar que nuevo_estado esté en las opciones (opcional pero recomendable)
        valid_values = [v for v, _ in EstadoActividad.choices]
        if nuevo_estado not in valid_values:
            return JsonResponse({'success': False, 'error': 'Valor de estado inválido'})

        periodo.estado = nuevo_estado
        periodo.save()
        return JsonResponse({'success': True, 'new_label': periodo.get_estado_display()})
    except Periodo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Periodo no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def generar_diccionario_registro(data, estado_anterior_json):
    cambios = {"actividad": {}, "encargados": [], "periodos": []}

    # --- Nombre de la actividad ---
    nuevo_nombre = data.get("nombre")
    if nuevo_nombre and nuevo_nombre != estado_anterior_json.get("nombre"):
        cambios["actividad"]["nombre"] = {
            "antes": estado_anterior_json.get("nombre"),
            "despues": nuevo_nombre,
            "tipo": "modificado"
        }

    # --- Encargados ---
    encargados_anteriores = {str(e["id"]): e for e in estado_anterior_json.get("encargados", [])}
    encargados_request = data.get("encargados", [])
    ids_en_request = []

    for e in encargados_request:
        eid = e.get("id")
        str_eid = str(eid) if eid else None
        ids_en_request.append(str_eid)

        if not str_eid:  # encargado nuevo sin ID
            if not any(ec.get("nombre") == e.get("nombre") and ec.get("correo") == e.get("correo")
                       for ec in estado_anterior_json.get("encargados", [])):
                cambios["encargados"].append({
                    "id": None,
                    "nombre": {"antes": None, "despues": e.get("nombre")},
                    "correo": {"antes": None, "despues": e.get("correo")},
                    "tipo": "creado"
                })
        else:
            anterior = encargados_anteriores.get(str_eid)
            if anterior:
                nombre_antes, correo_antes = anterior["nombre"], anterior["correo"]
                nombre_despues, correo_despues = e.get("nombre"), e.get("correo")

                if nombre_antes != nombre_despues or correo_antes != correo_despues:
                    cambios["encargados"].append({
                        "id": eid,
                        "nombre": {"antes": nombre_antes, "despues": nombre_despues},
                        "correo": {"antes": correo_antes, "despues": correo_despues},
                        "tipo": "modificado"
                    })
            else:
                # encargado existente agregado a la actividad
                cambios["encargados"].append({
                    "id": eid,
                    "nombre": {"antes": None, "despues": e.get("nombre")},
                    "correo": {"antes": None, "despues": e.get("correo")},
                    "tipo": "agregado"
                })

    # --- Eliminados: los que estaban antes y ya no están en el request ---
    for eid, e in encargados_anteriores.items():
        if eid not in ids_en_request:
            cambios["encargados"].append({
                "id": int(eid) if eid.isdigit() else eid,
                "nombre": {"antes": e.get("nombre"), "despues": None},
                "correo": {"antes": e.get("correo"), "despues": None},
                "tipo": "eliminado"
            })

    # --- Periodos ---
    def normalizar_id(pid):
        try:
            return int(pid)
        except (TypeError, ValueError):
            return None

    periodos_request = data.get("periodos", [])

    periodos_anteriores = {
        normalizar_id(p.get("id")): p
        for p in estado_anterior_json.get("periodos", [])
        if p.get("id") is not None
    }
    ids_periodos_request = []

    for p in periodos_request:
        if not p.get("f_inicio") and not p.get("f_fin"):
            continue  # ignorar filas vacías

        pid = normalizar_id(p.get("id"))
        if pid is not None:
            ids_periodos_request.append(pid)

        if pid is None:
            cambios["periodos"].append({
                "id": None,
                "fecha_inicio": {"antes": None, "despues": p.get("f_inicio")},
                "fecha_fin": {"antes": None, "despues": p.get("f_fin")},
                "tipo": "agregado"
            })
        else:
            anterior = periodos_anteriores.get(pid)
            if anterior and (anterior.get("f_inicio") != p.get("f_inicio") or anterior.get("f_fin") != p.get("f_fin")):
                cambios["periodos"].append({
                    "id": pid,
                    "fecha_inicio": {"antes": anterior.get("f_inicio"), "despues": p.get("f_inicio")},
                    "fecha_fin": {"antes": anterior.get("f_fin"), "despues": p.get("f_fin")},
                    "tipo": "modificado"
                })

    # --- Eliminados ---
    for pid, p in periodos_anteriores.items():
        if pid not in ids_periodos_request:
            cambios["periodos"].append({
                "id": pid,
                "fecha_inicio": {"antes": p.get("f_inicio"), "despues": None},
                "fecha_fin": {"antes": p.get("f_fin"), "despues": None},
                "tipo": "eliminado"
            })

    return cambios


def editar_actividad(request):
    #requets = {actividad: id, nombre: nuevo_nombre, periodos: [{id_periodo: 1, f_inicio: fecha_inicio, f_fin:fecha_fin},{id_periodo: '', f_inicio: fecha_inicio, f_fin:fecha_fin}]}
    if request.method == 'POST':
        
        # data = json.loads(request.body)
        # print("\n--- Datos recibidos en editar_actividad ---")
        # print(json.dumps(data, indent=4, ensure_ascii=False))
        # print("------------------------------------------\n")

        # actividad_id = data.get("id")
        # nombre = data.get("nombre")
        # encargados = data.get("encargados", [])
        # periodos = data.get("periodos", [])

        # print("------------------------------------------\n")
        # #printar el encargado 0
        # print(encargados[0]["nombre"])


        #cargar json
        data = json.loads(request.body)
        print("\n--- Datos recibidos en editar_actividad ---")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("------------------------------------------\n")


        #obtener id de la actividad y el nombre
        actividad = data.get('id')
        nuevo_nombre = data.get('nombre')

        # 1. Obtener Periodos ANTES de la modificación
        periodos_anteriores = Periodo.objects.filter(actividad=actividad, activo=True).order_by('fecha_inicio')
        periodos_json_anteriores = [{
            "id": p.id,
            "f_inicio": p.fecha_inicio.strftime('%Y-%m-%d'),
            "f_fin": p.fecha_fin.strftime('%Y-%m-%d')
        } for p in periodos_anteriores]
        
        # 2. Obtener Encargados ANTES de la modificación (usando la relación inversa)
        relaciones_encargados = Actividad_Encargado.objects.filter(actividad=actividad, activo=True)
        encargados_json_anteriores = []
        for relacion in relaciones_encargados:
             encargados_json_anteriores.append({
                "id": relacion.encargado.id,
                "nombre": relacion.encargado.nombre,
                "correo": relacion.encargado.correo_electronico
            })


        actividad_antes = get_object_or_404(ActividadBase, id=actividad)
        # 3. Crear el JSON de Estado Inicial
        estado_anterior_json = {
            "id": actividad_antes.id,
            "nombre": actividad_antes.nombre,
            "encargados": encargados_json_anteriores,
            "periodos": periodos_json_anteriores
        }
        
        # Revisar cambios antes de hacer nada
        cambios = generar_diccionario_registro(data, estado_anterior_json)
        if not cambios["actividad"] and not cambios["encargados"] and not cambios["periodos"]:
            return JsonResponse({"success": True, "message": "No hay cambios para guardar"})



        #obtener la actividad
        actividad = get_object_or_404(ActividadBase, id=actividad)

        # Actualizar nombre si se envió
        if nuevo_nombre:
            actividad.nombre = nuevo_nombre
            actividad.save()

        # Actualizar periodos si se envió
        periodos = data.get('periodos',[])
        ids_presentes_en_request = []
        for periodo_data in periodos:
            periodo_id = periodo_data.get('id') or None  # Normaliza

            f_inicio = periodo_data.get('f_inicio') or periodo_data.get('fecha_inicio')
            f_fin = periodo_data.get('f_fin') or periodo_data.get('fecha_fin')

            if periodo_id:  
                # Periodo existente → actualizar
                ids_presentes_en_request.append(periodo_id)

                periodo = get_object_or_404(Periodo, id=periodo_id, actividad=actividad)

                if periodo.fecha_inicio.strftime('%Y-%m-%d') != f_inicio:
                    periodo.fecha_inicio = f_inicio
                if periodo.fecha_fin.strftime('%Y-%m-%d') != f_fin:
                    periodo.fecha_fin = f_fin
                periodo.save()

            else:
                # Crear nuevo periodo
                nuevo_periodo = Periodo.objects.create(
                    actividad=actividad,
                    fecha_inicio=f_inicio,
                    fecha_fin=f_fin,
                    activo=True
                )
                ids_presentes_en_request.append(nuevo_periodo.id)


        Fechas_a_eliminar = Periodo.objects.filter(actividad=actividad, activo=True).exclude(
        id__in=ids_presentes_en_request)
        
        # para cada fecha actrualizar estado a False
        conteo_eliminado = 0
        for fecha in Fechas_a_eliminar:
            fecha.activo = False
            fecha.save()
            conteo_eliminado += 1




        encargados = data.get('encargados',[])
        ids_encargados_en_request = []
        for encargado_data in encargados:            
            encargado_id = encargado_data.get('id')
            if encargado_id != '':
                ids_encargados_en_request.append(encargado_id)
            nombre = encargado_data.get('nombre')
            correo = encargado_data.get('correo')
            if encargado_id != '':
                #print("Actualizando encargado existente")
                # Actualizar encargado existente
                encargado = get_object_or_404(Encargado, id=encargado_id)
                #comparar fechas del request con las ya existentes
                encargado.nombre = nombre
                encargado.correo_electronico = correo
                encargado.save()

                if not Actividad_Encargado.objects.filter(actividad=actividad, encargado=encargado).exists():
                    # Crear la relación si no existe
                    Actividad_Encargado.objects.create(
                        actividad=actividad,
                        encargado=encargado,
                        activo=True
                    ) 
                else:
                    # Asegurarse de que la relación esté activa
                    relacion = Actividad_Encargado.objects.get(actividad=actividad, encargado=encargado)
                    if not relacion.activo:
                        relacion.activo = True
                        relacion.save()
        
            else:
                # Crear nuevo encargado
                nuevo_encargado = Encargado.objects.create(
                    nombre=nombre,
                    correo_electronico=correo,
                    activo=True
                )
                Actividad_Encargado.objects.create(
                    actividad=actividad,
                    encargado=nuevo_encargado,
                    activo=True
                )

                ids_encargados_en_request.append(nuevo_encargado.id)
        encargados_a_eliminar = Actividad_Encargado.objects.filter(actividad_id=actividad, activo=True).exclude(
        encargado__id__in=ids_encargados_en_request )
        conteo_eliminado = 0
        for relacion in encargados_a_eliminar:
            # print("Eliminando encargado:", encargado.nombre)
            relacion.activo = False
            relacion.save()
            conteo_eliminado += 1

        try:
            # Obtener estado actual para el correo
            periodos_actuales = Periodo.objects.filter(actividad=actividad, activo=True).order_by('fecha_inicio')
            encargados_actuales = Actividad_Encargado.objects.filter(actividad=actividad, activo=True)

            estado_actual = {
                "nombre": actividad.nombre,
                "encargados": [{"nombre": e.encargado.nombre, "correo": e.encargado.correo_electronico} for e in encargados_actuales],
                "periodos": [{"f_inicio": p.fecha_inicio.strftime("%Y-%m-%d"), "f_fin": p.fecha_fin.strftime("%Y-%m-%d")} for p in periodos_actuales]
            }

            print("\n--- Cambios detectados ---")
            print(json.dumps(cambios, indent=4, ensure_ascii=False))
            print("------------------------------------------\n")
            # Registrar y notificar siempre
            registrar_y_notificar_cambios(actividad, cambios, estado_actual)

        except Exception as e:
            print(f"Error al registrar o notificar cambios: {e}")


    return JsonResponse({"success": True, "message": "Datos recibidos correctamente"})


def crear_actividad(request):
    #printar el request body
    if request.method == 'POST':
        data = json.loads(request.body)
        print("\n--- Datos recibidos en crear_actividad ---")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("------------------------------------------\n")

        return JsonResponse({'success': True, 'message': 'Funcionalidad en desarrollo'})


def obtener_historial(request, actividad_id):
    """
    Obtiene todos los registros de cambios de una actividad.
    Devuelve una lista de cambios ordenados por fecha descendente.
    """
    if request.method == 'GET':
        try:
            # Obtener la actividad
            actividad = get_object_or_404(ActividadBase, id=actividad_id)
            
            # Obtener todos los registros de cambios (ordenado por fecha_cambio desc)
            registros = actividad.registros_cambio.all()
            
            if not registros.exists():
                # No hay historial
                return JsonResponse([], safe=False)
            
            # Construir lista de cambios con fecha
            historial = []
            for registro in registros:
                print("Registro ID:", registro.id)
                print("Fecha de cambio:", registro.fecha_cambio)
                print("Cambios:", registro.cambios)
                historial.append({
                    'fecha_cambio': registro.fecha_cambio.strftime('%Y-%m-%d %H:%M:%S'),
                    'cambios': registro.cambios
                })


            print("\n--- Historial completo ---")
            print(json.dumps(historial, indent=4, ensure_ascii=False))
            print("------------------------------------------\n")
            # Retornar la lista completa
            return JsonResponse(historial, safe=False)
            
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


import json
import urllib.parse

# ID del dashboard y chart que quieres filtrar
DASHBOARD_ID = "6xq4LRdgrba"
CHART_ID = "13"  # ID del chart/filtro legacy en Superset

def reportes(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # 1️⃣ Creamos el filtro legacy dinámico
    preselect_filters = {
        CHART_ID: {
            "project_id": [str(proyecto.id)]
        }
    }
    print(preselect_filters)

    filters_encoded = urllib.parse.quote(json.dumps(preselect_filters))

    iframe_src = f"http://localhost:4003/superset"
    print(iframe_src)

    return render(request, 'vistas/reportes.html', {
        'proyecto': proyecto,
        'iframe_src': iframe_src
    })


