from django.core.mail import send_mail
from django.conf import settings
from proyectos.models import RegistroCambioActividad  # ajustar import si hace falta

def registrar_y_notificar_cambios(actividad, cambios):
    """
    Crea un registro de cambio de actividad y envía correo a encargados implicados.
    
    :param actividad: instancia de ActividadBase
    :param cambios: diccionario con la estructura definida
    :return: diccionario con destinatarios y mensaje generado
    """

    registro = RegistroCambioActividad.objects.create(
        actividad=actividad,
        cambios=cambios
    )

    actividad_nombre = actividad.nombre
    asunto = f"Cambios en la actividad: {actividad_nombre}"
    cuerpo = f"Se registraron los siguientes cambios en la actividad '{actividad_nombre}':\n\n"


    if "actividad" in cambios and "nombre" in cambios["actividad"]:
        antes = cambios["actividad"]["nombre"]["antes"]
        despues = cambios["actividad"]["nombre"]["despues"]
        cuerpo += f"• Nombre de la actividad: '{antes}' → '{despues}'\n"


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

        # todos los encargados del diccionario
        for grupo in ["antes", "despues"]:
            for e in cambios["encargados"].get(grupo, []):
                correo = e.get("correo")
                if correo:
                    destinatarios.add(correo)


    if "periodos" in cambios:
        periodos = cambios["periodos"]
        cuerpo += "\n\nCambios en periodos:\n"

        for mod in periodos.get("modificados", []):
            cuerpo += (
                f"  - {mod['nombre']}: "
                f"inicio {mod['fecha_inicio']['antes']} → {mod['fecha_inicio']['despues']}, "
                f"fin {mod['fecha_fin']['antes']} → {mod['fecha_fin']['despues']}\n"
            )
        for agr in periodos.get("agregados", []):
            cuerpo += f"  - Nuevo: {agr['nombre']} ({agr['fecha_inicio']} a {agr['fecha_fin']})\n"
        for elim in periodos.get("eliminados", []):
            cuerpo += f"  - Eliminado: {elim['nombre']} ({elim['fecha_inicio']} a {elim['fecha_fin']})\n"

    cuerpo += "\n\nPor favor, revisa los cambios en el sistema para más detalles."


    if destinatarios:
        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(destinatarios),
            fail_silently=False,
        )
