import base64
import json
import pickle
from redis import StrictRedis
from django.db import transaction
from django.conf import settings
from django.test import TestCase
from django_atomic_celery.testing import DjangoAtomicCeleryTestCaseMixin
from .tasks import task


class TaskTestCase(DjangoAtomicCeleryTestCaseMixin, TestCase):
    """Test case for tasks.
    """

    def setUp(self):
        super(TaskTestCase, self).setUp()

        # Set up Redis and clear the Celery key.
        self.redis = StrictRedis(settings.REDIS_HOST,
                                 settings.REDIS_PORT,
                                 settings.REDIS_DATABASE)
        self.redis.delete('celery')

    def assertNoScheduled(self):
        """Assert that no tasks are scheduled.
        """

        actual_task_count = self.redis.llen('celery')
        self.assertEqual(actual_task_count, 0)

    def assertScheduled(self, tasks):
        """Assert a specific number of tasks are scheduled.

        :param tasks:
            iterable of :class:`tuple` instances of
            ``(<task name>, <args>, <kwargs>)``.
        """

        actual_task_count = self.redis.llen('celery')
        self.assertEqual(actual_task_count, len(tasks))

        for t in tasks:
            raw_message = self.redis.lpop('celery')
            message = json.loads(raw_message)
            raw_body = base64.b64decode(message[u'body'])
            body = pickle.loads(raw_body)

            expected_name, expected_args, expected_kwargs = t
            self.assertEqual(body['task'], expected_name)
            if expected_args is not None:
                self.assertEqual(tuple(body['args']), tuple(expected_args))
            else:
                # args was not provided, compare with expected default
                self.assertEqual(tuple(body['args']), ())
            if expected_kwargs is not None:
                self.assertEqual(body['kwargs'], expected_kwargs)
            else:
                # kwargs was not provided, compare with expected default
                self.assertEqual(body['kwargs'], {})

    def _test_behavior(self, call, args=None, kwargs=None):
        # Task delayed outside transaction block is scheduled immediately.
        self.assertNoScheduled()
        if kwargs is None and args is None:
            call()
        elif kwargs is not None and args is None:
            call(kwargs=kwargs)
        elif kwargs is None and args is not None:
            call(args=args)
        else:
            call(args=args, kwargs=kwargs)
        self.assertScheduled([('tests.tasks.task', args, kwargs)])

        # Task delayed inside successful atomic transaction block is scheduled
        # after outermost transaction block is left.
        self.assertNoScheduled()
        with transaction.atomic():
            call(args, kwargs)
            self.assertNoScheduled()
        self.assertScheduled([('tests.tasks.task', args, kwargs)])

        self.assertNoScheduled()
        with transaction.atomic():
            call(args, kwargs)
            self.assertNoScheduled()
            with transaction.atomic():
                call(args, kwargs)
                self.assertNoScheduled()
            self.assertNoScheduled()
        self.assertScheduled([('tests.tasks.task', args, kwargs),
                              ('tests.tasks.task', args, kwargs)])

        # Task delayed inside failed atomic transaction block is not scheduled.
        self.assertNoScheduled()
        with self.assertRaises(ValueError):
            with transaction.atomic():
                call(args, kwargs)
                raise ValueError('Testing')
        self.assertNoScheduled()

        self.assertNoScheduled()
        with transaction.atomic():
            call(args, kwargs)
            with self.assertRaises(ValueError):
                with transaction.atomic():
                    call(args, kwargs)
                    raise ValueError('Testing')
            self.assertNoScheduled()
        self.assertScheduled([('tests.tasks.task', args, kwargs)])

    def test_delay(self):
        """@task(..).delay(..)
        """

        self._test_behavior(
            lambda args=None, kwargs=None: task.delay(*args, **kwargs), [], {})
        self._test_behavior(
            lambda args=None, kwargs=None: task.delay(*args, **kwargs),
            ['a', 1], {'a': 'b', '1': 2})

    def test_apply_async(self):
        """@task(..).apply_async(..)
        """

        self._test_behavior(task.apply_async, args=[], kwargs={})
        self._test_behavior(task.apply_async,
                            args=['a', 1],
                            kwargs={'a': 'b', '1': 2})
        self._test_behavior(task.apply_async)
        self._test_behavior(task.apply_async, args=())
        self._test_behavior(task.apply_async, kwargs={})
