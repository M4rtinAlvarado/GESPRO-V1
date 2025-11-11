import threading
from django.conf import settings
from django.core.mail import send_mail
from proyectos.models import RegistroCambioActividad
import json
import datetime


def send_mail_async(subject, message, from_email, recipient_list):
    """Envía correo en segundo plano para no bloquear la vista."""
    threading.Thread(
        target=send_mail,
        args=(subject, message, from_email, recipient_list),
        kwargs={"fail_silently": False},
    ).start()


def registrar_y_notificar_cambios(actividad, cambios, estado_actual):
    """
    Registra los cambios de la actividad y envía un correo mostrando los cambios realizados.
    
    :param actividad: instancia de ActividadBase
    :param cambios: diccionario generado por generar_diccionario_registro
    :param estado_actual: diccionario con el estado actual de la actividad, encargados y periodos
    """
    from django.core.mail import send_mail
    from django.conf import settings

    # 1. Guardar registro en la DB
    try:
        RegistroCambioActividad.objects.create(
            actividad=actividad,
            cambios=cambios,
            fecha_cambio=datetime.datetime.now()
        )
    except Exception as e:
        print(f"[ERROR] No se pudo crear el registro en DB: {e}")

    #printar cambios para debug
    print(f"[INFO] Cambios registrados para actividad {actividad.id}: {json.dumps(cambios, indent=2)}")

    # 2. Preparar correo
    asunto = f"Cambios en la actividad: {actividad.nombre}"
    cuerpo = f"Se han realizado cambios en la actividad '{actividad.nombre}':\n\n"

    # --- Nombre de la actividad ---
    if 'nombre' in cambios.get("actividad", {}):
        antes = cambios["actividad"]["nombre"]["antes"]
        despues = cambios["actividad"]["nombre"]["despues"]
        cuerpo += f"Nombre: {antes} → {despues}\n\n"
    else:
        cuerpo += f"Nombre: {estado_actual['nombre']}\n\n"

    # --- Encargados ---
    cuerpo += "Encargados:\n"
    destinatarios = set()
    for e in estado_actual.get("encargados", []):
        cuerpo += f"  - {e['nombre']} ({e.get('correo', 'sin correo')})\n"
        correo = e.get("correo")
        if correo:
            destinatarios.add(correo)

    if cambios.get("encargados"):
        cuerpo += "\nCambios en encargados:\n"
        for e in cambios["encargados"]:
            tipo = e["tipo"]
            if tipo == "agregado":
                cuerpo += f"  + Agregado: {e['nombre']} ({e.get('correo', 'sin correo')})\n"
            elif tipo == "eliminado":
                cuerpo += f"  - Eliminado: {e['nombre']} ({e.get('correo', 'sin correo')})\n"
            elif tipo == "modificado":
                antes = e.get("antes", {})
                cuerpo += f"  * Modificado: {e['nombre']} (correo: {antes.get('correo', 'sin correo')} → {e.get('correo', '')})\n"
    cuerpo += "\n"

    # --- Periodos ---
    cuerpo += "Periodos actuales:\n"
    for p in estado_actual.get("periodos", []):
        cuerpo += f"  - {p['f_inicio']} → {p['f_fin']}\n"

    if cambios.get("periodos"):
        cuerpo += "\nCambios en periodos:\n"
        for p in cambios["periodos"]:
            tipo = p["tipo"]
            if tipo == "agregado":
                cuerpo += f"  + Agregado: {p['fecha_inicio']['despues']} → {p['fecha_fin']['despues']}\n"
            elif tipo == "eliminado":
                cuerpo += f"  - Eliminado: {p['fecha_inicio']['antes']} → {p['fecha_fin']['antes']}\n"
            elif tipo == "modificado":
                cuerpo += (
                    f"  * Modificado:\n"
                    f"      Inicio: {p['fecha_inicio']['antes']} → {p['fecha_inicio']['despues']}\n"
                    f"      Fin   : {p['fecha_fin']['antes']} → {p['fecha_fin']['despues']}\n"
                )

    cuerpo += "\n."
    # 3. Enviar correo
    if destinatarios:
        try:
            send_mail_async(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(destinatarios),
            )
        except Exception as e:
            print(f"[ERROR] Error al enviar correo: {e}")
    else:
        print("[INFO] No hay destinatarios para enviar correo.")