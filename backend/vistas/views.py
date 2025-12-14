from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from proyectos.models import *
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Q        
from .gantt import calcular_gantt_data
import json
from vistas.alerta_cambios import registrar_y_notificar_cambios
from .dashboard import dashboard_view



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
        fechas_lista = []
        # Este filtro SÍ se aplica (correcto)
        for fecha in actividad.fechas.filter(activo=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            fechas_lista.append({
                "id": fecha.id,
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })

        # <-- CAMBIO AQUÍ: Filtramos solo encargados activos en esta relación
        consulta_2 = Actividad_Encargado.objects.filter(
            actividad=actividad, 
            activo=True 
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
            'activo': actividad.activo, 
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
        })

    # Actividades de difusión
    for actividad in actividades_difusion:
        fechas_lista = []
        # Este filtro SÍ se aplica (correcto)
        for fecha in actividad.fechas.filter(activo=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
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

    # Obtener todas las actividades normales (a través de linea_trabajo)
    # Cambiado: estado → activo, related_name es 'fechas' pero son objetos Periodo
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto,
        activo=True
    ).select_related('linea_trabajo').prefetch_related('fechas').order_by('linea_trabajo__id', 'fecha_creacion')
    
    # Obtener todas las actividades de difusión (directamente relacionadas con proyecto)
    # Cambiado: estado → activo, related_name es 'fechas' pero son objetos Periodo
    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto,
        activo=True
    ).prefetch_related('fechas').order_by('fecha_creacion')
    
    # Combinar todas las actividades en una lista
    todas_actividades = []

    for actividad in actividades_normales:
        # El related_name es 'fechas' pero son objetos Periodo, filtro por activo=True
        periodos = actividad.fechas.filter(activo=True)
        
        periodos_lista = []
        for periodo in periodos:
            periodos_lista.append({
                "fecha_inicio": periodo.fecha_inicio.strftime('%Y-%m-%d') if periodo.fecha_inicio else None,
                "fecha_fin": periodo.fecha_fin.strftime('%Y-%m-%d') if periodo.fecha_fin else None,
                "estado": periodo.estado  # Cada periodo tiene su propio estado
            })
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            "periodos": periodos_lista,  # Cambiado de fechas a periodos
            'tipo': 'Normal',
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
            'linea_trabajo_id': actividad.linea_trabajo.id if actividad.linea_trabajo else 999999,
            'orden_tipo': 1,
        })
    
    for actividad in actividades_difusion:
        # El related_name es 'fechas' pero son objetos Periodo, filtro por activo=True
        periodos = actividad.fechas.filter(activo=True)
        
        periodos_lista = []
        for periodo in periodos:
            periodos_lista.append({
                "fecha_inicio": periodo.fecha_inicio.strftime('%Y-%m-%d') if periodo.fecha_inicio else None,
                "fecha_fin": periodo.fecha_fin.strftime('%Y-%m-%d') if periodo.fecha_fin else None,
                "estado": periodo.estado  # Cada periodo tiene su propio estado
            })
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",
            'periodos': periodos_lista,  # Cambiado de fechas a periodos
            'tipo': 'Difusión',
            'linea_trabajo': 'Difusión',
            'linea_trabajo_id': 1000000,
            'orden_tipo': 2,
        })

    # Ordenar actividades por: 1) Tipo, 2) ID de línea de trabajo, 3) Fecha de inicio del primer periodo
    todas_actividades.sort(key=lambda x: (
        x['orden_tipo'],
        x['linea_trabajo_id'],
        x['periodos'][0]['fecha_inicio'] if x['periodos'] and x['periodos'][0]['fecha_inicio'] else '9999-12-31'
    ))
    
    # Agregar información sobre separadores de grupo
    linea_trabajo_anterior = None
    for i, actividad in enumerate(todas_actividades):
        actividad['mostrar_separador'] = (i == 0 or actividad['linea_trabajo'] != linea_trabajo_anterior)
        linea_trabajo_anterior = actividad['linea_trabajo']

    # Calcular columnas semanales y posiciones (ahora incluirá colores por periodo)
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

    # 1. Creamos un mapa de periodos anteriores (claves: INT ID, valor: dict de periodo)
    periodos_anteriores = {
        normalizar_id(p.get("id")): p
        for p in estado_anterior_json.get("periodos", [])
        if p.get("id") is not None
    }

    # 2. Creamos un Set de IDs que se enviaron en el request (para exclusión final rápida)
    # Usaremos esto como única fuente de verdad para los presentes.
    ids_presentes_request_set = set()

    for p in periodos_request:
        # Obtener IDs del Request (Entero o None)
        pid = normalizar_id(p.get("id"))
        
       
        f_inicio_request = p.get("fecha_inicio") or p.get("f_inicio")
        f_fin_request = p.get("fecha_fin") or p.get("f_fin")

       
        if pid is None:
            # Periodo nuevo
            cambios["periodos"].append({
                "id": None,
                "fecha_inicio": {"antes": None, "despues": f_inicio_request},
                "fecha_fin": {"antes": None, "despues": f_fin_request},
                "tipo": "agregado"
            })
        else:
            # Periodo existente
            ids_presentes_request_set.add(pid) # AÑADIDO: Registramos el ID en el Set
            anterior = periodos_anteriores.get(pid)
            
            if anterior: 
                # 3. Comprobación de Modificación
                # Las fechas anteriores están en "f_inicio" / "f_fin" en el estado anterior.
                if (anterior.get("f_inicio") != f_inicio_request or 
                    anterior.get("f_fin") != f_fin_request):
                    
                    cambios["periodos"].append({
                        "id": pid,
                        "fecha_inicio": {"antes": anterior.get("f_inicio"), "despues": f_inicio_request},
                        "fecha_fin": {"antes": anterior.get("f_fin"), "despues": f_fin_request},
                        "tipo": "modificado"
                    })

    # --- Eliminados de Periodos
    # Iteramos sobre el mapa anterior y verificamos si el ID NO está en el SET de IDs presentes.
    for pid, p in periodos_anteriores.items():
        if pid not in ids_presentes_request_set: 
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

        #cargar json
        data = json.loads(request.body)
        print("\n--- Datos recibidos en editar_actividad ---")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("------------------------------------------\n")


        #obtener id de la actividad y el nombre
        actividad_id = data.get('actividad_id') or data.get('id')
        if not actividad_id:
            return JsonResponse({"success": False, "error": "Falta el ID de la actividad a editar."}, status=400)
        print(actividad_id)
        nuevo_nombre = data.get('nombre')

        # 1. Obtener Periodos ANTES de la modificación
        periodos_anteriores = Periodo.objects.filter(actividad=actividad_id, activo=True).order_by('fecha_inicio')
        periodos_json_anteriores = [{
            "id": p.id,
            "f_inicio": p.fecha_inicio.strftime('%Y-%m-%d'),
            "f_fin": p.fecha_fin.strftime('%Y-%m-%d')
        } for p in periodos_anteriores]


        
        # 2. Obtener Encargados ANTES de la modificación (usando la relación inversa)
        relaciones_encargados = Actividad_Encargado.objects.filter(actividad=actividad_id, activo=True)
        encargados_json_anteriores = []
        for relacion in relaciones_encargados:
             encargados_json_anteriores.append({
                "id": relacion.encargado.id,
                "nombre": relacion.encargado.nombre,
                "correo": relacion.encargado.correo_electronico
            })


        actividad_antes = get_object_or_404(ActividadBase, id=actividad_id)
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
        actividad = get_object_or_404(ActividadBase, id=actividad_id)

        # Actualizar nombre si se envió
        if nuevo_nombre:
            actividad.nombre = nuevo_nombre
            actividad.save()

        # Actualizar periodos si se envió
        periodos = data.get('periodos',[])
        ids_presentes_en_request = []

        for periodo_data in periodos:

            periodo_id = periodo_data.get('id') or None 

            # Normalizar la fecha
            f_inicio = periodo_data.get('f_inicio') or periodo_data.get('fecha_inicio')
            f_fin = periodo_data.get('f_fin') or periodo_data.get('fecha_fin')

            if periodo_id:  

                if isinstance(periodo_id, int):
                    ids_presentes_en_request.append(periodo_id)
                else:

                    return JsonResponse({"success": False, "error": f"ID de período {periodo_id} no es un número válido."}, status=400)


                # Obtener el periodo para actualizar
                try:
                    # Usamos .get() en lugar de get_object_or_404 para manejo interno de errores.
                    periodo = Periodo.objects.get(id=periodo_id, actividad_id=actividad_id)
                except Periodo.DoesNotExist:
                    return JsonResponse({"success": False, "error": f"Período con ID {periodo_id} no existe para esta actividad."}, status=400)

                # Actualizar fechas
                if periodo.fecha_inicio.strftime('%Y-%m-%d') != f_inicio:
                    periodo.fecha_inicio = f_inicio
                if periodo.fecha_fin.strftime('%Y-%m-%d') != f_fin:
                    periodo.fecha_fin = f_fin
                periodo.save()

            else:
                # Crear nuevo periodo (periodo_id es None)
                nuevo_periodo = Periodo.objects.create(
                    actividad_id=actividad_id,
                    fecha_inicio=f_inicio,
                    fecha_fin=f_fin,
                    estado_valor=periodo_data.get('estado_valor', 'PEN'),
                    activo=True
                )
                # Se añade el ID (que es entero) generado por la DB
                ids_presentes_en_request.append(nuevo_periodo.id)


        Fechas_a_eliminar = Periodo.objects.filter(actividad=actividad_id, activo=True).exclude(
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

                if not Actividad_Encargado.objects.filter(actividad=actividad_id, encargado=encargado).exists():
                    # Crear la relación si no existe
                    Actividad_Encargado.objects.create(
                        actividad=actividad_id,
                        encargado=encargado,
                        activo=True
                    ) 
                else:
                    # Asegurarse de que la relación esté activa
                    relacion = Actividad_Encargado.objects.get(actividad=actividad_id, encargado=encargado)
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
                    actividad=actividad_id,
                    encargado=nuevo_encargado,
                    activo=True
                )

                ids_encargados_en_request.append(nuevo_encargado.id)
        encargados_a_eliminar = Actividad_Encargado.objects.filter(actividad=actividad_id, activo=True).exclude(
        encargado__id__in=ids_encargados_en_request )
        conteo_eliminado = 0
        for relacion in encargados_a_eliminar:
            # print("Eliminando encargado:", encargado.nombre)
            relacion.activo = False
            relacion.save()
            conteo_eliminado += 1

        try:
            # Obtener estado actual para el correo
            periodos_actuales = Periodo.objects.filter(actividad=actividad_id, activo=True).order_by('fecha_inicio')
            encargados_actuales = Actividad_Encargado.objects.filter(actividad=actividad_id, activo=True)

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


def reportes(request, proyecto_id):
   context = dashboard_view(request, proyecto_id)
   return render(request, 'vistas/reportes.html', context)
    


def crear_actividad(request):
    try:
        data = json.loads(request.body)
        
        # Datos del request
        proyecto_id = data.get('proyecto_id')
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        producto_nombre = data.get('producto')
        lineas_nombres = data.get('lineas_trabajo', [])
        encargados_data = data.get('encargados', [])
        periodos_data = data.get('periodos', [])

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'})

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

def crear_actividad(request):
    try:
        data = json.loads(request.body)
        
        # Datos del request
        proyecto_id = data.get('proyecto_id')
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        producto_nombre = data.get('producto')
        lineas_nombres = data.get('lineas_trabajo', [])
        encargados_data = data.get('encargados', [])
        periodos_data = data.get('periodos', [])

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'})

        proyecto = get_object_or_404(Proyecto, id=proyecto_id)

        with transaction.atomic():
            
            # --- 1. Crear la Actividad Base ---
            actividad_nueva = None

            if tipo == 'Normal':
                if not lineas_nombres:
                    return JsonResponse({'success': False, 'error': 'Falta línea de trabajo'})
                
                nombre_linea = lineas_nombres[0]
                linea_obj = LineaTrabajo.objects.filter(proyecto=proyecto, nombre=nombre_linea).first()
                
                if not linea_obj:
                    return JsonResponse({'success': False, 'error': f'Línea "{nombre_linea}" no encontrada'})

                actividad_nueva = Actividad.objects.create(nombre=nombre, linea_trabajo=linea_obj)

            elif tipo == 'Difusion':
                actividad_nueva = ActividadDifusion.objects.create(nombre=nombre, proyecto=proyecto)
                
                for nombre_linea in lineas_nombres:
                    linea_obj = LineaTrabajo.objects.filter(proyecto=proyecto, nombre=nombre_linea).first()
                    if linea_obj:
                        ActividadDifusion_Linea.objects.create(
                            actividad=actividad_nueva, 
                            linea_trabajo=linea_obj, 
                            estado=True  # Este modelo SÍ usa 'estado' según tu código anterior
                        )
                
                if producto_nombre:
                    ProductoAsociado.objects.create(nombre=producto_nombre, actividad_base=actividad_nueva)
            else:
                return JsonResponse({'success': False, 'error': 'Tipo de actividad inválido'})

            # --- 2. Procesar Encargados (CORREGIDO) ---
            for enc in encargados_data:
                nombre_enc = enc.get('nombre')
                correo_enc = enc.get('correo', '').strip()

                encargado_obj = None
                
                # Criterio de búsqueda seguro
                criterio = Q()
                if correo_enc:
                    criterio |= Q(correo_electronico=correo_enc)
                if nombre_enc:
                    criterio |= Q(nombre=nombre_enc)
                
                if criterio:
                    # Soluciona error "returned 14": Toma el primero y ignora duplicados
                    encargado_obj = Encargado.objects.filter(criterio).first()

                # Si no existe, crear
                if not encargado_obj:
                    encargado_obj = Encargado.objects.create(
                        nombre=nombre_enc,
                        correo_electronico=correo_enc
                    )
                else:
                    if correo_enc and not encargado_obj.correo_electronico:
                        encargado_obj.correo_electronico = correo_enc
                        encargado_obj.save()

                # Crear la relación
                Actividad_Encargado.objects.create(
                    actividad=actividad_nueva,
                    encargado=encargado_obj,
                    activo=True  # <--- CORRECCIÓN IMPORTANTE: Tu modelo usa 'activo', no 'estado'
                )

            # --- 3. Procesar Periodos ---
            for per in periodos_data:
                f_inicio = per.get('fecha_inicio')
                f_fin = per.get('fecha_fin')
                estado_val = per.get('estado_valor', 'PEN')

                if f_inicio and f_fin:
                    Periodo.objects.create(
                        actividad=actividad_nueva,
                        fecha_inicio=f_inicio,
                        fecha_fin=f_fin,
                        estado=estado_val,
                        activo=True
                    )

            # 4. Actualizar Proyecto
            proyecto.ultima_modificacion = datetime.now()
            proyecto.save()

        return JsonResponse({'success': True, 'message': 'Actividad creada correctamente'})

    except Exception as e:
        print(f"Error Backend: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)