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

    # --- 1. Guardar registro en la DB ---
    try:
        RegistroCambioActividad.objects.create(
            actividad=actividad,
            cambios=cambios,
            fecha_cambio=datetime.datetime.now()
        )
    except Exception as e:
        print(f"[ERROR] No se pudo crear el registro en DB: {e}")

    print(f"[INFO] Cambios registrados para actividad {actividad.id}: {json.dumps(cambios, indent=2)}")

    # --- 2. Preparar correo ---
    asunto = f"Cambios en la actividad: {actividad.nombre}"
    cuerpo = f"Se han realizado cambios en la actividad '{actividad.nombre}':\n\n"

    # --- Nombre de la actividad ---
    if "nombre" in cambios.get("actividad", {}):
        antes = cambios["actividad"]["nombre"]["antes"]
        despues = cambios["actividad"]["nombre"]["despues"]
        cuerpo += f"Nombre: {antes or '—'} → {despues or '—'}\n\n"
    else:
        cuerpo += f"Nombre: {estado_actual['nombre']}\n\n"

    # --- Encargados actuales ---
    cuerpo += "Encargados actuales:\n"
    destinatarios = set()

    for e in estado_actual.get("encargados", []):
        correo = e.get("correo")
        cuerpo += f"  - {e['nombre']} ({correo or 'sin correo'})\n"
        if correo:
            destinatarios.add(correo)

    # --- Incluir los eliminados como destinatarios también ---
    for e in cambios.get("encargados", []):
        if e.get("tipo") == "eliminado":
            correo_antes = e.get("correo", {}).get("antes")
            if correo_antes:
                destinatarios.add(correo_antes)

    # --- Cambios en encargados ---
    cambios_visibles = [e for e in cambios.get("encargados", []) if e["tipo"] in ("agregado", "eliminado", "modificado", "creado")]
    if cambios_visibles:
        cuerpo += "\nCambios en encargados:\n"
        for e in cambios_visibles:
            nombre_antes = e["nombre"].get("antes")
            nombre_despues = e["nombre"].get("despues")
            correo_antes = e["correo"].get("antes")
            correo_despues = e["correo"].get("despues")
            tipo = e["tipo"]

            if tipo == "agregado":
                cuerpo += f"  + Agregado: {nombre_despues} ({correo_despues or 'sin correo'})\n"
            elif tipo == "eliminado":
                cuerpo += f"  - Eliminado: {nombre_antes} ({correo_antes or 'sin correo'})\n"
            elif tipo == "modificado":
                cuerpo += f"  * Modificado:\n"
                if nombre_antes != nombre_despues:
                    cuerpo += f"      Nombre: {nombre_antes} → {nombre_despues}\n"
                if correo_antes != correo_despues:
                    cuerpo += f"      Correo: {correo_antes or '—'} → {correo_despues or '—'}\n"
            elif tipo == "creado":
                cuerpo += f"  + Creado: {nombre_despues} ({correo_despues or 'sin correo'})\n"

    cuerpo += "\n"

    # --- Periodos actuales ---
    cuerpo += "Periodos actuales:\n"
    for p in estado_actual.get("periodos", []):
        cuerpo += f"  - {p['f_inicio']} → {p['f_fin']}\n"

    # --- Cambios en periodos ---
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

    # --- 3. Enviar correo ---
    if destinatarios:
        try:
            send_mail_async(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(destinatarios),
            )
            print(f"[INFO] Correo enviado a: {', '.join(destinatarios)}")
        except Exception as e:
            print(f"[ERROR] Error al enviar correo: {e}")
    else:
        print("[INFO] No hay destinatarios para enviar correo.")
