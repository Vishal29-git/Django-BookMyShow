# bookmyseat/celery.py
# This file sets up Celery for our Django project

import os
from celery import Celery

# Tell Celery where our Django settings are
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')

# Create the Celery application
app = Celery('bookmyseat')

# Load settings from Django's settings.py (any setting starting with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically find tasks.py files in all your apps
app.autodiscover_tasks()