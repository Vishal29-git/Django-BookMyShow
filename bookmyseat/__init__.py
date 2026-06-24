# This makes sure Celery starts whenever Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)