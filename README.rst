django_atomic_celery - Atomic transaction aware Celery tasks for Django
=======================================================================

.. image:: https://travis-ci.org/adamchainz/django_atomic_celery.png?branch=master
        :target: https://travis-ci.org/adamchainz/django_atomic_celery

Don't Use This Library
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
`django-atomic-celery`. A new, "don't use me" version that breaks on import will be pushed soon to PyPI to propagate
this warning.

Old Readme Continues
--------------------

``django_atomic_celery`` provides a Django 1.6-1.7 compatible approach to transactionally aware Celery task scheduling.

To install ``django_atomic_celery``, do yourself a favor and don't use anything other than `pip <http://www.pip-installer.org/>`_:

.. code-block:: bash

   $ pip install django-atomic-celery

Add ``django_atomic_celery`` along with its dependency, ``django_atomic_signals``, to the list of installed apps in your settings file:

.. code-block:: python

   INSTALLED_APPS = (
       'django_atomic_signals',
       'django_atomic_celery',
       ..
   )


Usage
-----

Using ``django_atomic_celery`` is exactly like using Celery the way you normally would. However, instead of importing Celery's variant of the ``task`` decorator, import it from ``django_atomic_celery``:

.. code-block:: python

   from django_atomic_celery import task


   @task
   def simple_task():
       ..


   @task(ignore_result=True, max_retries=3, default_retry_delay=10)
   def retrying_task(arg):
       ..

If you use Celery 3.1 and its internal integration of Django, you can choose to instantiate your Celery app providing the atomic task class as the ``task_cls`` argument to have all tasks be atomic transaction aware. Based on an example from `the Celery documentation <http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html>`_ this is done as follows:

.. code-block:: python

   from celery import Celery

   ..
   app = Celery('proj', task_cls='django_atomic_celery:PostTransactionTask')
   ..
