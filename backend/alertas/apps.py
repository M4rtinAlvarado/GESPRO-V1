# tu_app/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AlertasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alertas'

    def ready(self):
        # Usamos un signal para que se ejecute solo después de que 
        # las tablas de la base de datos existan
        post_migrate.connect(setup_scheduled_tasks, sender=self)

def setup_scheduled_tasks(sender, **kwargs):
    from django_q.models import Schedule
    from django_q.tasks import schedule

    # Nombre único para la tarea
    task_name = 'Chequeo Minutal de Alertas'

    if not Schedule.objects.filter(name=task_name).exists():
        schedule(
            'alertas.tasks.enviar_alertas_programadas',
            schedule_type=Schedule.MINUTES,
            minutes=1,
            name=task_name
        )