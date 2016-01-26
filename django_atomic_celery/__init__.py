class PackageDeadException(Exception):
    pass

raise PackageDeadException(
    "This package is dead, you should upgrade using the instructions at "
    "https://github.com/adamchainz/django_atomic_celery"
)
