from django.shortcuts import render, redirect
from proyectos.models import *
from django.db.models import Prefetch
from .forms import UploadExcelForm
import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from .import_gantt import importar_gantt, informacion_proyecto, separar_tablas_excel, FormatoInvalidoError


# Create your views here.
def validar_datos_formulario(nombre_proyecto, archivo):
    """Valida los datos del formulario y retorna lista de errores"""
    errores = []
    
    # Validar nombre del proyecto
    if not nombre_proyecto or not nombre_proyecto.strip():
        errores.append("El nombre del proyecto es obligatorio.")
    else:
        # Validar caracteres especiales problemáticos
        caracteres_invalidos = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in caracteres_invalidos:
            if char in nombre_proyecto:
                errores.append(f"El nombre del proyecto no puede contener el carácter: '{char}'")
                break
    
    # Validar archivo
    if not archivo:
        errores.append("Por favor selecciona un archivo Excel.")
    else:
        # Validar extensión
        nombre_archivo = archivo.name.lower()
        if not (nombre_archivo.endswith('.xlsx') or nombre_archivo.endswith('.xls')):
            errores.append(f"El archivo debe ser Excel (.xlsx o .xls)")
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if archivo.size > max_size:
            errores.append(f"El archivo es demasiado grande. Tamaño máximo: 10MB")
    
    return errores

def verificar_proyecto(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            nombre_proyecto = form.cleaned_data['nombre_proyecto']
            archivo = request.FILES.get('archivo')
            
            # Validar datos del formulario solo si hay datos
            if nombre_proyecto or archivo:
                errores_validacion = validar_datos_formulario(nombre_proyecto, archivo)
                if errores_validacion:
                    for error in errores_validacion:
                        messages.error(request, error)
                    return render(request, 'excel/importar_proyecto.html', {'form': form})
            
            try:
                ruta_tmp = f"/tmp/{archivo.name}"
                with open(ruta_tmp, 'wb+') as destino:
                    for chunk in archivo.chunks():
                        destino.write(chunk)
                
                df_normales, df_difusion = separar_tablas_excel(archivo)
                info_proyecto = informacion_proyecto(df_normales, df_difusion)
                info_proyecto['Nombre_del_Proyecto'] = nombre_proyecto
                
                return render(request, 'excel/importar_proyecto.html', {
                    'info_proyecto': info_proyecto, 
                    'form': form, 
                    'archivo': ruta_tmp, 
                    'mostrar_modal': True
                })
                
            except FormatoInvalidoError as e:
                messages.error(request, f"Error de formato: {str(e)}")
            except FileNotFoundError:
                messages.error(request, "No se pudo procesar el archivo. Intenta nuevamente.")
            except PermissionError:
                messages.error(request, "No se tienen permisos para procesar el archivo.")
            except ValueError as e:
                messages.error(request, f"Error en los datos del archivo: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
        else:
            # Si el formulario no es válido y se envió con datos
            if request.POST.get('nombre_proyecto') or request.FILES.get('archivo'):
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en {field}: {error}")
    else:
        form = UploadExcelForm()

    return render(request, 'excel/importar_proyecto.html', {'form': form})

def importar_proyecto(request):
    if request.method == 'POST':
        nombre_proyecto = request.POST.get('nombre_proyecto')
        ruta_tmp = request.POST.get('archivo')
        
        if not nombre_proyecto:
            messages.error(request, "No se proporcionó el nombre del proyecto.")
            return redirect('verificar_proyecto')
        
        if not ruta_tmp:
            messages.error(request, "No se proporcionó la ruta del archivo.")
            return redirect('verificar_proyecto')
            
        try:
            with open(ruta_tmp, 'rb') as archivo:
                importar_gantt(nombre_proyecto, archivo)
                # No mostrar mensaje de éxito como solicitaste
                return redirect('proyectos')  # Redirigir a la lista de proyectos
                
        except FileNotFoundError:
            messages.error(request, "No se encontró el archivo temporal. Intenta subir el archivo nuevamente.")
        except FormatoInvalidoError as e:
            messages.error(request, f"Error de formato: {str(e)}")
        except ValueError as e:
            messages.error(request, f"Error en los datos: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error al importar el proyecto: {str(e)}")
            
        return redirect('verificar_proyecto')
 

def descargar_plantilla(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
    if os.path.exists(ruta_archivo):
        return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename='plantilla.xlsx')
    else:
        raise Http404("Archivo no encontrado")
    

def datos_exportar(request):
    if request.method == 'POST':
        proyecto_id = request.POST.get('proyecto_id')
        lista_actividades= []
        # Prefetch encargados
        encargados_prefetch = Prefetch(
            'actividad_encargados',
            queryset=Actividad_Encargado.objects.select_related('encargado')
                .only('encargado__nombre'),
            to_attr='encargados_cache'
        )

        # Prefetch períodos (solo fechas)
        periodos_prefetch = Prefetch(
            'fechas',
            queryset=Periodo.objects.only('fecha_inicio', 'fecha_fin'),
            to_attr='periodos_cache'
        )

        # Prefetch productos asociados (solo nombre)
        productos_prefetch = Prefetch(
            'productos_asociados',
            queryset=ProductoAsociado.objects.only('nombre'),
            to_attr='productos_cache'
        )

        actividades = (
            Actividad.objects            
            .select_related('linea_trabajo')  
            .prefetch_related(
                encargados_prefetch,
                periodos_prefetch,
                productos_prefetch
            )
            .only(
                'id',
                'n_act',
                'nombre',
                'linea_trabajo__nombre',
            )  
        )


        for act in actividades:

            responsables = [ae.encargado.nombre for ae in act.encargados_cache]

            periodos = [(p.fecha_inicio.strftime("%d/%m/%Y"), p.fecha_fin.strftime("%d/%m/%Y")) for p in act.periodos_cache]

            producto = act.productos_cache[0].nombre if act.productos_cache else None

            fila = [
                act.n_act,
                act.linea_trabajo.nombre,
                responsables,
                producto,
                periodos
            ]

            lista_actividades.append(fila)
        
        lista_actividades_difusion = []

        encargados_prefetch = Prefetch(
            'actividad_encargados',
            queryset=Actividad_Encargado.objects.select_related('encargado')
                .only('encargado__nombre'),
            to_attr='encargados_cache'
        )

        # Prefetch períodos (solo fechas)
        periodos_prefetch = Prefetch(
            'fechas',
            queryset=Periodo.objects.only('fecha_inicio', 'fecha_fin'),
            to_attr='periodos_cache'
        )

        # Productos asociados (muchos)
        productos_prefetch = Prefetch(
            'productos_asociados',
            queryset=ProductoAsociado.objects.only('nombre'),
            to_attr='productos_cache'
        )

        # Líneas de trabajo (muchas)
        lineas_prefetch = Prefetch(
            'actividad_lineas',
            queryset=ActividadDifusion_Linea.objects.select_related('linea_trabajo')
                .only('linea_trabajo__nombre'),
            to_attr='lineas_cache'
        )

        actividades = (
            ActividadDifusion.objects
            .select_related('proyecto')
            .prefetch_related(
                encargados_prefetch,
                periodos_prefetch,
                productos_prefetch,
                lineas_prefetch
            )
            .only(
                'id',
                'n_act',
                'nombre',
                'proyecto__nombre'
            )
        )

        for act in actividades:

            responsables = [ae.encargado.nombre for ae in act.encargados_cache]

            periodos = [(p.fecha_inicio.strftime("%d/%m/%Y"), p.fecha_fin.strftime("%d/%m/%Y")) for p in act.periodos_cache]

            productos = [p.nombre for p in act.productos_cache]

            lineas = [rel.linea_trabajo.nombre for rel in act.lineas_cache]

            fila = [
                act.n_act,
                act.proyecto.nombre,
                lineas,
                responsables,
                productos,
                periodos
            ]

            lista_actividades_difusion.append(fila)

    #     print("Actividades Normales:")
    #     print(lista_actividades)
    #     print("Actividades de Difusión:")
    #     print(lista_actividades_difusion)
    # return redirect('proyectos')
