django_atomic_celery - Atomic transaction aware Celery tasks for Django
=======================================================================

.. image:: https://travis-ci.org/nickbruun/django_atomic_celery.png?branch=master
        :target: https://travis-ci.org/nickbruun/django_atomic_celery

``django_atomic_celery`` provides a Django 1.6 compatible approach to transactionally aware approach to Celery task scheduling.


Installation
------------

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
