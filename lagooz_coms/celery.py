from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lagooz_coms.settings')

app = Celery('lagooz_coms')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Explicitly import tasks so Celery registers them
# import accounts.tasks
