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
            self.assertEqual(tuple(body['args']), tuple(expected_args))
            self.assertEqual(body['kwargs'], expected_kwargs)

    def _test_behavior(self, call, args, kwargs):
        # Task delayed outside transaction block is scheduled immediately.
        self.assertNoScheduled()
        call(args, kwargs)
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

        self._test_behavior(lambda a, k: task.delay(*a, **k), [], {})
        self._test_behavior(lambda a, k: task.delay(*a, **k),
                            ['a', 1],
                            {'a': 'b', '1': 2})

    def test_apply_async(self):
        """@task(..).apply_async(..)
        """

        self._test_behavior(lambda a, k: task.apply_async(a, k), [], {})
        self._test_behavior(lambda a, k: task.apply_async(a, k),
                            ['a', 1],
                            {'a': 'b', '1': 2})
