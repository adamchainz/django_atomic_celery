from django.dispatch import Signal


django_atomic_celery_loaded = Signal(providing_args=[])
"""Django atomic Celery loaded.
"""
