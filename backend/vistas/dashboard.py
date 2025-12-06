
import plotly.express as px
from django.shortcuts import render
import json
from plotly.offline import plot
from proyectos.models import *
from django.db.models import Count
from plotly.offline import plot
import pandas as pd
from django.shortcuts import get_object_or_404

def grafico_view(request,context):
    # 1. Consulta de Datos y Agregación
    # Contar cuántas actividades hay por cada estado
    estados_conteo = ActividadBase.objects.values('estado').annotate(
        count=Count('estado')
    ).order_by('-count')

    # Si no hay actividades, retornar un gráfico vacío o mensaje
    if not estados_conteo:
        context = {'grafico_html': '<h2>No hay actividades registradas.</h2>'}
        return render(request, 'dashboard/grafico_estados.html', context)
    
    # 2. Preparar los datos para Plotly
    
    # Crear un DataFrame simple para Plotly
    df = pd.DataFrame(list(estados_conteo))
    
    # Mapear los códigos de estado (ej: 'PEN') a las etiquetas legibles (ej: 'Pendiente')
    estado_labels = {
        value: label 
        for value, label in ActividadBase._meta.get_field('estado').choices
    }
    df['estado_nombre'] = df['estado'].map(estado_labels)

    # 3. Crear el Gráfico de Torta con Plotly Express
    fig = px.pie(
        df, 
        values='count', 
        names='estado_nombre',
        title='Distribución de Actividades por Estado',
        hole=0.3, # Puedes crear un gráfico de anillo (donut chart)
        color_discrete_sequence=px.colors.sequential.RdBu # Paleta de colores
    )

    # Configurar el diseño para una mejor visualización en HTML
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title="Estado",
    )

    # 4. Convertir la figura de Plotly en un DIV HTML
    plot_div = plot(
        fig, 
        output_type='div', 
        include_plotlyjs=True, # Incluir la librería JS de Plotly
        config={'displayModeBar': False} # Oculta la barra de herramientas de Plotly
    )
    context = {
        'grafico_html': plot_div
    }
    return context

def dashboard_view(request, id_proyecto):
    context = {}
    context = grafico_view(request,context)
    context['proyecto'] = get_object_or_404(Proyecto, id=id_proyecto)
    return context