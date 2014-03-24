from django_atomic_celery import task


@task
def task(*arg, **kwargs):
    pass
