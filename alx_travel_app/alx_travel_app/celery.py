import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

celery = Celery('alx_travel_app')
celery.config_from_object('django.conf:settings',namespace='CELERY')

celery.autodiscover_tasks()