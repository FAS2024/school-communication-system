import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lagooz_coms.settings')

app = Celery('lagooz_coms')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
