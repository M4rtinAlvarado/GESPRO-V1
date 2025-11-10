import threading
from django.conf import settings
from django.core.mail import send_mail
from proyectos.models import RegistroCambioActividad
import json


def send_mail_async(subject, message, from_email, recipient_list):
    """Envía correo en segundo plano para no bloquear la vista."""
    threading.Thread(
        target=send_mail,
        args=(subject, message, from_email, recipient_list),
        kwargs={"fail_silently": False},
    ).start()


def registrar_y_notificar_cambios(actividad, cambios):
    """
    Crea un registro de cambio de actividad y envía correo a encargados implicados.
    
    :param actividad: instancia de ActividadBase
    :param cambios: diccionario con la estructura:
        {
            "actividad": {"nombre": {"antes": ..., "despues": ...}},
            "encargados": {"antes": [...], "despues": [...]},
            "periodos": {"modificados": [...], "agregados": [...], "eliminados": [...]}
        }
    """
    from django.core.mail import send_mail
    from django.conf import settings

    # Registrar cambios en DB
    try:
        # printar cambios
        print("=== Registrando cambios en la actividad ===")
        print(json.dumps(cambios, indent=4, ensure_ascii=False))

        registro = RegistroCambioActividad.objects.create(
            actividad=actividad,
            cambios=cambios
        )
    except Exception as e:
        print(f"[ERROR] No se pudo crear el registro en DB: {e}")
        registro = None

    actividad_nombre = actividad.nombre
    asunto = f"Cambios en la actividad: {actividad_nombre}"
    cuerpo = f"Se registraron los siguientes cambios en la actividad '{actividad_nombre}':\n\n"

    # --- Cambio de nombre ---
    if "actividad" in cambios and "nombre" in cambios["actividad"]:
        antes = cambios["actividad"]["nombre"]["antes"]
        despues = cambios["actividad"]["nombre"]["despues"]
        cuerpo += f"• Nombre de la actividad: '{antes}' → '{despues}'\n"

    # --- Cambios en encargados ---
    destinatarios = set()
    if "encargados" in cambios:
        antes = cambios["encargados"].get("antes", [])
        despues = cambios["encargados"].get("despues", [])

        nombres_antes = {e["nombre"] for e in antes}
        nombres_despues = {e["nombre"] for e in despues}

        eliminados = nombres_antes - nombres_despues
        agregados = nombres_despues - nombres_antes

        if eliminados:
            cuerpo += f"\n• Encargados removidos: {', '.join(eliminados)}"
        if agregados:
            cuerpo += f"\n• Encargados agregados: {', '.join(agregados)}"

        # Agregar todos los correos de encargados antes y después (si existen)
        for grupo in ["antes", "despues"]:
            for e in cambios["encargados"].get(grupo, []):
                correo = e.get("correo")
                if correo:
                    destinatarios.add(correo)

    # --- Cambios en periodos ---
    if "periodos" in cambios:
        periodos = cambios["periodos"]
        if periodos.get("modificados") or periodos.get("agregados") or periodos.get("eliminados"):
            cuerpo += "\n\nCambios en periodos:\n"

            for mod in periodos.get("modificados", []):
                cuerpo += (
                    f"  - Modificado: inicio {mod['fecha_inicio']['antes']} → {mod['fecha_inicio']['despues']}, "
                    f"fin {mod['fecha_fin']['antes']} → {mod['fecha_fin']['despues']}\n"
                )
            for agr in periodos.get("agregados", []):
                cuerpo += f"  - Agregado: {agr['fecha_inicio']} → {agr['fecha_fin']}\n"
            for elim in periodos.get("eliminados", []):
                cuerpo += f"  - Eliminado: {elim['fecha_inicio']} → {elim['fecha_fin']}\n"

    cuerpo += "\nPor favor, revisa los cambios en el sistema para más detalles."


    if destinatarios:
        try:
            send_mail_async(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(destinatarios),
            )
            print("[INFO] Correo enviado correctamente (en segundo plano).")
        except Exception as e:
            print(f"[ERROR] Error al enviar correo: {e}")
    else:
        print("[INFO] No hay destinatarios para enviar correo.")