
import plotly.express as px
from django.shortcuts import render, get_object_or_404
import json
from plotly.offline import plot
from proyectos.models import Actividad, ActividadDifusion, ActividadBase, ActividadDifusion_Linea, Proyecto
from django.db.models import Count, Value, CharField, F, Q
import pandas as pd

def datos_dashboard(id_proyecto):
    """
    Realiza una única consulta optimizada a la base de datos para obtener
    los datos base requeridos por el dashboard (gráfico de torta y barras).

    Retorna un diccionario con DataFrames listos para graficar.
    """
    
    # --- 1. CONSULTA BASE UNIFICADA (Para el gráfico de Barras Apiladas) ---
    
    # a) Actividades Normales: 
    # Usando Actividad para obtener ActividadBase a través del puntero de herencia.
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto_id=id_proyecto
    ).annotate(
        linea_nombre=F('linea_trabajo__nombre'),
        # El estado está en ActividadBase, el puntero de herencia es 'actividadbase_ptr'
        actividad_estado=F('actividadbase_ptr__periodo__estado'), # <-- CAMBIO AQUI: Asumiendo Periodo es el que tiene el estado actual
        target_act_id=F('id'), 
    ).values('linea_nombre', 'actividad_estado', 'target_act_id').distinct() # Agrego distinct() para evitar duplicados si hay múltiples Periodos

    
    # b) Actividades de Difusión (genera múltiples filas por actividad/línea):
    actividades_difusion = ActividadDifusion_Linea.objects.filter(
        linea_trabajo__proyecto_id=id_proyecto,
        actividad__proyecto_id=id_proyecto
    ).annotate(
        linea_nombre=F('linea_trabajo__nombre'),
        # El estado está en Periodo, relacionado a ActividadBase de ActividadDifusion
        actividad_estado=F('actividad__periodo__estado'), # <-- CAMBIO AQUI: Asumiendo Periodo es el que tiene el estado actual
        target_act_id=F('actividad__id'), 
    ).values('linea_nombre', 'actividad_estado', 'target_act_id').distinct() # Agrego distinct()

    
    # c) Combinación de datos en Pandas (Dataset Maestro)
    data_combinada = list(actividades_normales) + list(actividades_difusion)
    
    if not data_combinada:
        return {'df_maestro': pd.DataFrame(), 'df_torta': pd.DataFrame(), 'df_barras': pd.DataFrame(), 'estado_labels': {}}

    df_maestro = pd.DataFrame(data_combinada)
    
    
    # --- 2. PRE-PROCESAMIENTO PARA GRÁFICOS ---
    
    # **IMPORTANTE**: Tus modelos no definen el campo 'estado' directamente en ActividadBase,
    # sino que lo defines en el modelo 'Periodo', que apunta a 'ActividadBase'. 
    # El estado real de la actividad debe inferirse, probablemente desde el Periodo
    # más reciente, o asumiendo que solo hay un Periodo relevante.

    # **ASUNCION CLAVE**: He ajustado las consultas Django (arriba) para usar `F('...periodo__estado')`.
    # Esto es una simplificación: si una actividad tiene múltiples `Periodo`s, esto podría 
    # generar múltiples filas por actividad/línea, por lo que he añadido `.distinct()` 
    # en las consultas. **Si necesitas el estado del período más reciente, requeriría una anotación
    # más compleja o un pre-procesamiento de datos diferente.**

    # Obtener las etiquetas de estado solo una vez
    # Ahora, el estado se obtiene del modelo Periodo, pero usa las choices de EstadoActividad.
    estado_labels = {
        value: label 
        for value, label in ActividadBase._meta.get_field('actividad_encargados').model.periodo.field.related_model.estado.field.choices
    }
    
    # a) Generar DataFrame para Gráfico de Torta (Estados)
    # Contamos la cantidad de actividades ÚNICAS por estado.
    # Esto es CORRECTO: Cuenta actividades únicas (target_act_id) por su estado.
    df_torta = df_maestro.drop_duplicates(subset=['target_act_id']).groupby('actividad_estado').size().reset_index(name='count')
    df_torta['estado_nombre'] = df_torta['actividad_estado'].map(estado_labels)
    
    
    # b) Generar DataFrame para Gráfico de Barras Apiladas (Líneas y Estados)
    # Contamos la asignación (una fila por Línea/Actividad/Estado), lo cual es lo que se quiere para la carga de trabajo.
    df_barras = df_maestro.groupby(['linea_nombre', 'actividad_estado']).size().reset_index(name='count')
    df_barras.rename(columns={'linea_nombre': 'Linea_Trabajo'}, inplace=True)
    df_barras['estado_nombre'] = df_barras['actividad_estado'].map(estado_labels)
    
    
    # --- 3. RETORNAR DATA ---
    return {
        'df_torta': df_torta,
        'df_barras': df_barras,
        'estado_labels': estado_labels # Útil para mapeo en funciones de gráfico
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

from django.db.models import Count, Value, CharField, F


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

def dashboard_view(request, id_proyecto):
    context = {}
    datos = datos_dashboard(id_proyecto)
    context.update(graf_est_act_tr(datos['df_torta']))
    context.update(graf_bar_lin_est(datos['df_barras'], datos['estado_labels']))
    print (context)
    context['proyecto'] = get_object_or_404(Proyecto, id=id_proyecto)
    return context