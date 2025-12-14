
import plotly.express as px
from django.shortcuts import render, get_object_or_404
import json
from plotly.offline import plot
from proyectos.models import *
from django.db.models import Count, Value, CharField, F, Q, Min
import pandas as pd
from datetime import date

import pandas as pd
from datetime import date
from django.db.models import F, Q, Min, Max, Count, Case, When
from proyectos.models import Actividad, ActividadDifusion_Linea, Periodo, EstadoActividad, Proyecto, Alerta 
from dateutil.relativedelta import relativedelta 

def datos_dashboard(id_proyecto):
    """
    Realiza consultas optimizadas a la BD y usa Pandas para generar los tres DataFrames:
    df_torta, df_barras, df_area_plot.
    """

    # --- 1. EXTRACCIÓN DE DATOS DE LA BD ---

    # A. Consulta para Gráfico de Barras y Torta (Actividad, Estado, Línea)
    
    # a. Actividades Normales: 
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto_id=id_proyecto
    ).annotate(
        linea_nombre=F('linea_trabajo__nombre'),
        actividad_estado=F('actividadbase_ptr__fechas__estado'), 
        target_act_id=F('id'), 
    ).values('linea_nombre', 'actividad_estado', 'target_act_id').distinct()
    
    # b. Actividades de Difusión (genera múltiples filas por actividad/línea):
    actividades_difusion = ActividadDifusion_Linea.objects.filter(
        linea_trabajo__proyecto_id=id_proyecto,
        actividad__proyecto_id=id_proyecto
    ).annotate(
        linea_nombre=F('linea_trabajo__nombre'),
        actividad_estado=F('actividad__fechas__estado'), 
        target_act_id=F('actividad__id'), 
    ).values('linea_nombre', 'actividad_estado', 'target_act_id').distinct()

    # c. Combinación para el Dataset Maestro de Barras/Torta
    data_combinada = list(actividades_normales) + list(actividades_difusion)
    
    if not data_combinada:
        # Si no hay actividades, no hay datos para ningún gráfico.
        return {
            'df_torta': pd.DataFrame(), 
            'df_barras': pd.DataFrame(), 
            'df_area_plot': pd.DataFrame(), 
            'estado_labels': {}
        }

    df_barras_torta_maestro = pd.DataFrame(data_combinada)

    # B. Consulta para Gráfico de Área (Fechas y Estado por Actividad)
    
    # Obtenemos todos los periodos del proyecto para calcular las fechas clave.
    project_periods = Periodo.objects.filter(
        Q(actividad__actividad__linea_trabajo__proyecto_id=id_proyecto) |
        Q(actividad__actividaddifusion__proyecto_id=id_proyecto)          
    ).values(
        'actividad_id', 
        'fecha_inicio', 
        'fecha_fin', 
        'estado'
    ).distinct()

    df_fechas = pd.DataFrame(list(project_periods))
    
    # --- 2. PRE-PROCESAMIENTO DE DATOS EN PANDAS ---
    
    # 2.1 Generar Etiquetas de Estado
    estado_labels = {
        value: label 
        for value, label in EstadoActividad.choices
    }

    # 2.2 Cálculos para df_torta (Actividades Únicas por Estado)
    df_torta = df_barras_torta_maestro.drop_duplicates(subset=['target_act_id']).groupby('actividad_estado').size().reset_index(name='count')
    df_torta['estado_nombre'] = df_torta['actividad_estado'].map(estado_labels)
    
    # 2.3 Cálculos para df_barras (Asignaciones por Línea y Estado)
    df_barras = df_barras_torta_maestro.groupby(['linea_nombre', 'actividad_estado']).size().reset_index(name='count')
    df_barras.rename(columns={'linea_nombre': 'Linea_Trabajo'}, inplace=True)
    df_barras['estado_nombre'] = df_barras['actividad_estado'].map(estado_labels)

    # 2.4 Cálculos para df_area_plot (Conteo Mensual Planificado vs Completado)
    
    # Encontrar la fecha clave para cada actividad única
    df_planned = df_fechas.groupby('actividad_id')['fecha_inicio'].min().reset_index(name='Fecha_Planificada')
    
    # Fecha de Finalización (La fecha de fin más temprana de un Periodo con estado 'COM')
    df_completed_periods = df_fechas[df_fechas['estado'] == EstadoActividad.COMPLETADA.value]
    if not df_completed_periods.empty:
        df_completed = df_completed_periods.groupby('actividad_id')['fecha_fin'].min().reset_index(name='Fecha_Completada')
    else:
        df_completed = pd.DataFrame(columns=['actividad_id', 'Fecha_Completada'])
    
    df_area_maestro = pd.merge(df_planned, df_completed, on='actividad_id', how='left')
    
    # Convertir a Timestamp para manipulación de fechas en Pandas
    df_area_maestro['Fecha_Planificada'] = pd.to_datetime(df_area_maestro['Fecha_Planificada'])
    df_area_maestro['Fecha_Completada'] = pd.to_datetime(df_area_maestro['Fecha_Completada'])

    # Rango de tiempo
    if df_area_maestro['Fecha_Planificada'].empty or df_area_maestro['Fecha_Planificada'].min() is pd.NaT:
        df_area_plot = pd.DataFrame()
    else:
        min_date = df_area_maestro['Fecha_Planificada'].min().to_period('M').start_time 
        max_date = pd.to_datetime(date.today()).to_period('M').start_time + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        date_range = pd.date_range(start=min_date, end=max_date, freq='MS')
        
        data_for_plot = []
        
        # Calcular los conteos NO acumulativos por mes
        for month_start in date_range:
            month_end = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)
            
            # Conteo Planificado: Actividades cuyo inicio (Fecha_Planificada) cae dentro de este mes.
            monthly_planned = df_area_maestro[
                (df_area_maestro['Fecha_Planificada'] >= month_start) & 
                (df_area_maestro['Fecha_Planificada'] <= month_end)
            ]['actividad_id'].nunique()
            
            # Conteo Completado: Actividades cuya finalización (Fecha_Completada) cae dentro de este mes.
            monthly_completed = df_area_maestro[
                (df_area_maestro['Fecha_Completada'].notna()) & 
                (df_area_maestro['Fecha_Completada'] >= month_start) & 
                (df_area_maestro['Fecha_Completada'] <= month_end)
            ]['actividad_id'].nunique()
            
            if monthly_planned > 0 or monthly_completed > 0:
                data_for_plot.extend([
                    {'Fecha_Plot': month_start, 'Cantidad': monthly_planned, 'Tipo': 'Actividades Planificadas (Inicio)'},
                    {'Fecha_Plot': month_start, 'Cantidad': monthly_completed, 'Tipo': 'Actividades Completadas (Finalizadas)'}
                ])

        df_area_plot = pd.DataFrame(data_for_plot)


    # --- 3. RETORNAR TODOS LOS DATOS ---
    return {
        'df_torta': df_torta,
        'df_barras': df_barras,
        'df_area_plot': df_area_plot, # Nuevo DataFrame
        'estado_labels': estado_labels
    }



def obtener_metricas_resumen(id_proyecto):
    """
    Realiza las consultas necesarias a la BD para calcular métricas clave de resumen
    del proyecto (totales, progreso, retrasos, alertas).
    """
    
    hoy = date.today()
    
    # --- 1. CONSULTA BASE PARA ESTADOS Y TOTALES (Sin cambios) ---
    
    # a. Actividades Normales: 
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto_id=id_proyecto
    ).annotate(
        target_act_id=F('id'), 
        actividad_estado=F('actividadbase_ptr__fechas__estado'),
    ).values('target_act_id', 'actividad_estado').distinct()

    # b. Actividades de Difusión:
    actividades_difusion = ActividadDifusion_Linea.objects.filter(
        actividad__proyecto_id=id_proyecto
    ).annotate(
        target_act_id=F('actividad__id'), 
        actividad_estado=F('actividad__fechas__estado'),
    ).values('target_act_id', 'actividad_estado').distinct()

    data_combinada = list(actividades_normales) + list(actividades_difusion)
    
    if not data_combinada:
        return {
            'total_actividades': 0, 'actividades_completadas': 0, 
            'actividades_retrasadas': 0, 'progreso_general': 0.0, 
            'dias_proyecto_restantes': None, 'dias_proyecto_totales': None,
            'progreso_temporal': 0.0, 'alertas_pendientes_num': 0
        }

    df_actividades_unicas = pd.DataFrame(data_combinada).drop_duplicates(subset=['target_act_id', 'actividad_estado'])

    # --- 2. CÁLCULO DE MÉTRICAS SIMPLES (Sin cambios) ---
    
    total_actividades = df_actividades_unicas['target_act_id'].nunique()
    
    actividades_completadas = df_actividades_unicas[
        (df_actividades_unicas['actividad_estado'] == EstadoActividad.COMPLETADA.value) |
        (df_actividades_unicas['actividad_estado'] == EstadoActividad.TERMINADA.value)
    ]['target_act_id'].nunique()
    
    progreso_general = (actividades_completadas / total_actividades * 100) if total_actividades > 0 else 0.0

    # --- 3. CONSULTA PARA RETRASOS Y DATOS DEL PROYECTO ---

    # a. Datos de Fechas de Periodo para Retrasos
    df_fechas = pd.DataFrame(list(
        Periodo.objects.filter(
            Q(actividad__actividad__linea_trabajo__proyecto_id=id_proyecto) |
            Q(actividad__actividaddifusion__proyecto_id=id_proyecto)          
        ).values('actividad_id', 'fecha_fin', 'estado').distinct()
    ))
    
    # b. Actividades Retrasadas (Lógica en Pandas)
    df_retraso = df_fechas.groupby('actividad_id').agg(
        ultima_fecha_fin=('fecha_fin', 'max'),
        es_completada=('estado', lambda x: any(e in x.values for e in [EstadoActividad.COMPLETADA.value, EstadoActividad.TERMINADA.value]))
    ).reset_index()

    df_retraso['ultima_fecha_fin'] = pd.to_datetime(df_retraso['ultima_fecha_fin'])
    hoy_dt = pd.to_datetime(hoy)

    actividades_retrasadas = df_retraso[
        (df_retraso['ultima_fecha_fin'] < hoy_dt) & 
        (df_retraso['es_completada'] == False)
    ]['actividad_id'].nunique()
    
    # c. Días Totales/Restantes del Proyecto (Consulta y Lógica de tiempo)
    
    # NUEVA CONSULTA: Obtener la fecha de inicio REAL del proyecto (fecha de inicio MIN de TODOS los Periodos del proyecto)
    min_fecha_inicio_periodo = Periodo.objects.filter(
        Q(actividad__actividad__linea_trabajo__proyecto_id=id_proyecto) |
        Q(actividad__actividaddifusion__proyecto_id=id_proyecto)          
    ).aggregate(min_fecha=Min('fecha_inicio'))['min_fecha']
    
    # Obtener la fecha de fin del Proyecto (directamente del modelo Proyecto)
    proyecto_obj = Proyecto.objects.filter(id=id_proyecto).values('fecha_fin').first()
    fecha_fin_proyecto = proyecto_obj['fecha_fin'] if proyecto_obj else None
    
    
    dias_proyecto_totales = None
    dias_proyecto_restantes = None
    progreso_temporal = 0.0
    
    fecha_inicio = min_fecha_inicio_periodo
    fecha_fin = fecha_fin_proyecto
    
    if fecha_inicio and fecha_fin:
        fecha_fin_dt = pd.to_datetime(fecha_fin)
        fecha_inicio_dt = pd.to_datetime(fecha_inicio)
        
        dias_proyecto_totales = (fecha_fin_dt - fecha_inicio_dt).days
        
        # Calcular días restantes (segun el hoy de python)
        dias_proyecto_restantes = (fecha_fin_dt - hoy_dt).days
        
        # Lógica de progreso temporal
        dias_proyecto_pasados = (hoy_dt - fecha_inicio_dt).days
        progreso_temporal = (dias_proyecto_pasados / dias_proyecto_totales * 100) if dias_proyecto_totales > 0 else 0.0
        progreso_temporal = max(0, min(100, progreso_temporal))

    # d. Alertas Pendientes (Nueva Consulta)
    # ATENCIÓN: El path `periodo__actividad__actividad__linea_trabajo__proyecto_id` 
    # asume que quieres filtrar por actividades normales. Para cubrir ambas:
    alertas_pendientes_num = Alerta.objects.filter(
        Q(periodo__actividad__actividad__linea_trabajo__proyecto_id=id_proyecto) |
        Q(periodo__actividad__actividaddifusion__proyecto_id=id_proyecto),
        enviado=False,
        activo=True
    ).count()

    # --- 4. RETORNAR MÉTRICAS ---
    return {
        'total_actividades': total_actividades,
        'actividades_completadas': actividades_completadas,
        'actividades_retrasadas': actividades_retrasadas,
        'progreso_general': round(progreso_general, 1),
        # Aseguramos que dias_proyecto_restantes no sea negativo
        'dias_proyecto_restantes': max(0, dias_proyecto_restantes) if dias_proyecto_restantes is not None else None,
        'dias_proyecto_totales': dias_proyecto_totales,
        'progreso_temporal': round(progreso_temporal, 1),
        'alertas_pendientes_num': alertas_pendientes_num,
    }

def graf_est_act_tr(df_torta):
    """Genera el HTML del gráfico de anillo de distribución de estados."""
    
    if df_torta.empty:
        return {'grafico_torta_estado': '<h2>No hay actividades registradas para este proyecto.</h2>'}


    fig = px.pie(
        df_torta, 
        values='count', 
        names='estado_nombre',
        title='Distribución de Todas las Actividades por Estado',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Dark2
    )

    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>Estado</b>: %{label}<br>" +
                      "<b>Actividades</b>: %{value}<br>" +
                      "<b>Porcentaje</b>: %{percent}<extra></extra>"
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title="Estado de Actividad",
    )

    plot_div = plot(
        fig, 
        output_type='div', 
        include_plotlyjs=True, 
        config={'displayModeBar': True}
    )

    # Devolvemos un diccionario con una clave específica
    return {'grafico_torta_estado': plot_div}



def truncar_nombre_linea(nombre, max_chars=35):
    """
    Trunca el nombre de la línea si excede max_chars y añade '...'.
    """
    if len(nombre) > max_chars:
        return nombre[:max_chars].strip() + "..."
    return nombre

def graf_bar_lin_est(df_barras, estado_labels):
    """
    Genera el HTML del gráfico de barras horizontal apiladas,
    incluyendo actividades normales y actividades de difusión 
    contabilizadas en todas sus líneas de trabajo asociadas.
    """
    
    
    df_barras.rename(columns={'linea_nombre': 'Linea_Trabajo'}, inplace=True)
    # 1. Almacenar el nombre original en una columna nueva
    df_barras['Nombre_Completo'] = df_barras['Linea_Trabajo']
    
    # 2. Aplicar el truncamiento a la columna que se usará en el eje Y
    df_barras['Linea_Trabajo'] = df_barras['Linea_Trabajo'].apply(
        lambda x: truncar_nombre_linea(x, max_chars=35)
    )
    # 5. Crear el Gráfico de Barras Apiladas Horizontal con Plotly Express
    
    fig = px.bar(
        df_barras, 
        x='count', 
        y='Linea_Trabajo',
        color='estado_nombre', # Divide las barras por el estado
        orientation='h',      # Hace las barras horizontales
        title='Distribución de Cargas de Trabajo por Línea y Estado',
        category_orders={"estado_nombre": list(estado_labels.values())},
        color_discrete_sequence=px.colors.qualitative.Dark2,
    )
    
    # 6. Configurar el Diseño y el Mouseover (Hover)
    fig.update_layout(
        xaxis_title="Número de Asignaciones (Actividad en Línea)",
        yaxis_title="Línea de Trabajo",
        legend_title="Estado",
        margin=dict(l=100, r=20, t=50, b=20),
        barmode='stack'
    )

    fig.update_traces(
        hovertemplate="<b>Línea:</b> %{y}<br>" +
                      "<b>Estado:</b> %{data.name}<br>" +
                      "<b>Asignaciones:</b> %{x}<extra></extra>"
    )

    # 7. Convertir la figura a DIV HTML
    plot_div = plot(
        fig, 
        output_type='div', 
        include_plotlyjs=False, 
        config={'displayModeBar': True}
    )

    return {'grafico_barras_lineas': plot_div}



def graf_area_temporal(df_plot):
    """
    Genera el HTML del gráfico de área de actividades (mensuales, NO acumulativas y NO apiladas).
    """
    
    if df_plot.empty:
        return {'grafico_area_temporal': '<h2>No hay datos temporales para mostrar.</h2>'}
    
    category_orders = {
        "Tipo": ['Actividades Planificadas (Inicio)', 'Actividades Completadas (Finalizadas)']
    }

    # Se elimina el argumento 'stackgroup' para resolver el TypeError 
    # y para cumplir con el requisito de no apilar.
    fig = px.area(
        df_plot, 
        x='Fecha_Plot', 
        y='Cantidad', 
        color='Tipo',
        title='Inicio Planificado y Finalización Real por Mes', 
        category_orders=category_orders,
        color_discrete_sequence=['#AEC7E8', '#1F77B4'], 
        # stackgroup ha sido ELIMINADO.
    )

    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Cantidad Mensual de Actividades", # Título ajustado
        legend_title="Tipo de Avance",
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        xaxis=dict(tickformat="%b %Y")
    )
    
    
    fig.update_traces(
        # Eliminar el texto interno en un gráfico de área
        hovertemplate="<b>%{x|%b %Y}</b><br>" +
                      "<b>%{fullData.name}</b>: %{y}<extra></extra>"
    )

    plot_div = plot(
        fig, 
        output_type='div', 
        include_plotlyjs=True, 
        config={'displayModeBar': True}
    )

    return {'grafico_area_temporal': plot_div}

def dashboard_view(request, id_proyecto):
    context = {}
    datos = datos_dashboard(id_proyecto)
    context.update(obtener_metricas_resumen(id_proyecto))
    context.update(graf_est_act_tr(datos['df_torta']))
    context.update(graf_bar_lin_est(datos['df_barras'], datos['estado_labels']))
    context.update(graf_area_temporal(datos['df_area_plot']))


    context['proyecto'] = get_object_or_404(Proyecto, id=id_proyecto)
    return context