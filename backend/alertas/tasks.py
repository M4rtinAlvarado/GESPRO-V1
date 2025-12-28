# alertas/tasks.py
import zoneinfo
from django.utils import timezone
from django.core.mail import send_mail
from proyectos.models import Alerta, Actividad_Encargado

def enviar_alertas_programadas():
    # Localizamos el tiempo actual a Chile para una comparación precisa
    tz_chile = zoneinfo.ZoneInfo("America/Santiago")
    ahora = timezone.now().astimezone(tz_chile)

    alertas = Alerta.objects.filter(fecha_envio__lte=ahora, enviado=False, activo=True)

    for alerta in alertas:
        actividad_obj = alerta.periodo.actividad
 
        correos = Actividad_Encargado.objects.filter(
            actividad=actividad_obj, 
            activo=True
        ).values_list('encargado__correo_electronico', flat=True)
        
        if correos:
            try:
                send_mail(
                    subject=f"Alerta: {actividad_obj.nombre}",
                    message=f"Recuerda que hoy debes realizar la actividad: {actividad_obj.nombre}",
                    from_email=None, 
                    recipient_list=list(correos),
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error SMTP en Alerta {alerta.id}: {e}")
                continue 

        alerta.enviado = True
        alerta.save()