django_atomic_celery - Atomic transaction aware Celery tasks for Django
=======================================================================

.. image:: https://travis-ci.org/adamchainz/django_atomic_celery.png?branch=master
        :target: https://travis-ci.org/adamchainz/django_atomic_celery

Don't Use This Package
----------------------

This library uses `django-atomic-signals`_. Unfortunately this is not a great way of achieving "don't run this code
until the transaction commits" any more. There is plenty of extra description on `django-atomic-signals' README
<django-atomic-signals>`_, and also on the similar library `django-transaction-signals`_, by Django core developer
Aymeric.

.. _django-atomic-signals: https://github.com/adamchainz/django_atomic_signals
.. _django-transaction-signals: https://github.com/aaugustin/django-transaction-signals

If you want a supported method of executing a celery task on commit, then:

- on Django >= 1.9, use the built-in on_commit_ hook
- on Django < 1.9, use `django-transaction-hooks`_ (the original source of 1.9's ``on_commit``)

.. _on_commit: https://docs.djangoproject.com/en/dev/topics/db/transactions/#django.db.transaction.on_commit
.. _django-transaction-hooks: https://django-transaction-hooks.readthedocs.org/

Both give examples with celery tasks so you are in good hands.

If your project is still using this library, please migrate. You will need to remove `django-atomic-signals` as well as
`django-atomic-celery`.

The current version of `django-atomic-celery`, 2.0.0, simply errors upon import, directing you here.
