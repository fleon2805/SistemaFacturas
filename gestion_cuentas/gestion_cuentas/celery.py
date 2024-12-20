from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from kombu import Queue

# Establece el módulo de configuración predeterminado de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_cuentas.settings')

# Crea la aplicación Celery
app = Celery('gestion_cuentas', broker='redis://localhost:6379/0')

app.conf.update(
    task_queues = ('default',),
    worker_pool = 'solo',  # Esto evitará el uso de procesos múltiples
)

app.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('celery', routing_key='celery'),
)

# Configura Celery para que use el archivo de configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre automáticamente las tareas en las aplicaciones de Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
