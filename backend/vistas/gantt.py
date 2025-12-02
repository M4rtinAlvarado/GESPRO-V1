from datetime import datetime, timedelta
import math


def calcular_gantt_data(actividades):
    if not actividades:
        return {
            'columnas_semanales': [], 
            'week_width': 100, 
            'total_weeks': 0,
            'total_width': 320,
            'start_date': None,
            'end_date': None
        }
    
    # Recopilar todas las fechas del proyecto
    todas_fechas = _extraer_fechas_actividades(actividades)
    
    if not todas_fechas:
        return {
            'columnas_semanales': [], 
            'week_width': 100, 
            'total_weeks': 0,
            'total_width': 320,
            'start_date': None,
            'end_date': None
        }
    
    # Calcular rango de fechas ajustado a semanas completas
    start_of_week, end_of_week, total_weeks = _calcular_rango_semanal(todas_fechas)
    
    # Configuración de dimensiones
    week_width = 100  # Ancho estándar de columna semanal
    
    # Generar columnas semanales con metadatos
    columnas_semanales = _generar_columnas_semanales(start_of_week, total_weeks, week_width)
    
    # Calcular posiciones de barras para cada actividad
    _calcular_posiciones_actividades(actividades, start_of_week, week_width)
    
    return {
        'columnas_semanales': columnas_semanales,
        'week_width': week_width,
        'total_weeks': total_weeks,
        'total_width': 320 + (total_weeks * week_width),
        'start_date': start_of_week,
        'end_date': end_of_week
    }


def _extraer_fechas_actividades(actividades):
    """Extrae todas las fechas de los periodos de las actividades"""
    todas_fechas = []
    
    for actividad in actividades:
        # Cambiado: fechas → periodos
        if actividad.get('periodos'):
            for periodo_obj in actividad['periodos']:
                if periodo_obj['fecha_inicio'] and periodo_obj['fecha_fin']:
                    fecha_inicio = datetime.strptime(periodo_obj['fecha_inicio'], '%Y-%m-%d').date()
                    fecha_fin = datetime.strptime(periodo_obj['fecha_fin'], '%Y-%m-%d').date()
                    todas_fechas.extend([fecha_inicio, fecha_fin])
    
    return todas_fechas


def _calcular_rango_semanal(fechas):
    fecha_min = min(fechas)
    fecha_max = max(fechas)
    
    days_to_monday = fecha_min.weekday()
    start_of_week = fecha_min - timedelta(days=days_to_monday + 7)
    
    days_to_sunday = 6 - fecha_max.weekday()
    end_of_week = fecha_max + timedelta(days=days_to_sunday + 7)
    total_days = (end_of_week - start_of_week).days
    total_weeks = math.ceil(total_days / 7)
    
    return start_of_week, end_of_week, total_weeks


def _generar_columnas_semanales(start_date, total_weeks, week_width):

    meses_es = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    
    columnas_semanales = []
    today = datetime.now().date()
    
    for week in range(total_weeks):
        week_start = start_date + timedelta(days=week * 7)
        week_end = week_start + timedelta(days=6)
        

        is_current_week = week_start <= today <= week_end
        
        columnas_semanales.append({
            'week_index': week,
            'week_start': week_start,
            'week_end': week_end,
            'left_px': week * week_width,
            'width_px': week_width,
            'is_current_week': is_current_week,
            'month_name': meses_es[week_start.month],
            'day_number': week_start.day
        })
    
    return columnas_semanales


def _calcular_posiciones_actividades(actividades, start_date, week_width):
    """Calcula posiciones de barras para cada periodo de cada actividad"""
    for actividad in actividades:
        actividad['periodos_calculados'] = []
        
        # Cambiado: fechas → periodos
        if not actividad.get('periodos'):
            continue
            
        for i, periodo_obj in enumerate(actividad['periodos']):
            if not (periodo_obj['fecha_inicio'] and periodo_obj['fecha_fin']):
                continue
                
            # Parsear fechas
            fecha_inicio = datetime.strptime(periodo_obj['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(periodo_obj['fecha_fin'], '%Y-%m-%d').date()
            
            duracion_dias = (fecha_fin - fecha_inicio).days + 1
            dias_desde_inicio = (fecha_inicio - start_date).days
            dias_hasta_fin = (fecha_fin - start_date).days
            
            # Calcular semanas que abarca el periodo
            week_inicio = dias_desde_inicio // 7
            week_fin = dias_hasta_fin // 7
            semanas_ocupadas = week_fin - week_inicio + 1
            
            # Vista semanal: siempre ocupa semana completa donde inicia
            left_px = week_inicio * week_width
            width_px = semanas_ocupadas * week_width
            
            # Vista mensual: ancho proporcional a las semanas que ocupa
            left_px_monthly = _escalar_posicion_mensual(left_px)
            width_px_monthly = _calcular_ancho_mensual_real(semanas_ocupadas)
            
            # Obtener clase de color según el estado del periodo
            color_class = _obtener_color_por_estado(periodo_obj.get('estado'))
            
            actividad['periodos_calculados'].append({
                'periodo': i + 1,
                'fecha_inicio': periodo_obj['fecha_inicio'],
                'fecha_fin': periodo_obj['fecha_fin'],
                'estado': periodo_obj.get('estado'),  # Estado individual del periodo
                'color_class': color_class,  # Clase Tailwind para colorear la barra
                'left_px': left_px,
                'width_px': width_px,
                'left_px_monthly': left_px_monthly,
                'width_px_monthly': width_px_monthly,
                'duracion_dias': duracion_dias,
                'ocupa_semana_completa': True
            })


def _escalar_posicion_mensual(left_px_semanal):
    return int((left_px_semanal * 25) / 100)


def _calcular_ancho_mensual(width_px_semanal):
    width_escalado = int((width_px_semanal * 25) / 100)
    return max(width_escalado, 18)


def _calcular_ancho_mensual_real(semanas_ocupadas):
    """Calcula el ancho real para vista mensual basado en semanas ocupadas"""
    ancho_por_semana = 25  # 25px por semana en vista mensual
    ancho_total = semanas_ocupadas * ancho_por_semana
    return max(ancho_total, 18)  # Mínimo 18px


def _obtener_color_por_estado(estado):
    """Mapea el código de estado del periodo a una clase Tailwind de color"""
    colores = {
        'PEN': 'bg-red-500',      # Pendiente → Rojo
        'LPC': 'bg-yellow-500',   # Listo para comenzar → Amarillo
        'EPR': 'bg-blue-500',     # En progreso → Azul
        'COM': 'bg-green-500',    # Completado → Verde
        'TER': 'bg-purple-500'    # Terminado → Morado
    }
    return colores.get(estado, 'bg-gray-400')  # Por defecto gris si no se reconoce