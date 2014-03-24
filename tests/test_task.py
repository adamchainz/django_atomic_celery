from redis import StrictRedis
from django.db import connections, transaction, DEFAULT_DB_ALIAS
from django.conf import settings
from django.test import TestCase
from .tasks import task


class TaskTestCase(TestCase):
    """Test case for tasks.
    """

    def setUp(self):
        super(TaskTestCase, self).setUp()

        # Exit the atomic block to make sure that signals are handled properly,
        # as Django uses transactions to wrap test cases.
        self.connection = connections[DEFAULT_DB_ALIAS]

        for alias, atomic in self.atomics.items():
            connections[alias].needs_rollback = True
            atomic.__exit__(None, None, None)

        # Set up Redis and clear the Celery key.
        self.redis = StrictRedis(settings.REDIS_HOST,
                                 settings.REDIS_PORT,
                                 settings.REDIS_DATABASE)
        self.redis.delete('celery')

    def tearDown(self):
        for atomic in self.atomics.values():
            atomic.__enter__()

        super(TaskTestCase, self).tearDown()

    def assertScheduledCount(self, task_count):
        """Assert a specific number of tasks are scheduled.

        :param task_count: Number of tasks expected to be scheduled.
        """

        actual_task_count = self.redis.llen('celery')
        self.redis.delete('celery')
        self.assertEqual(actual_task_count,
                         task_count)

    def test_delay(self):
        """@task(..).delay(..)
        """

        # Task delayed outside transaction block is scheduled immediately.
        self.assertScheduledCount(0)
        task.delay()
        self.assertScheduledCount(1)

        # Task delayed inside successful atomic transaction block is scheduled
        # after outermost transaction block is left.
        self.assertScheduledCount(0)
        with transaction.atomic():
            task.delay()
            self.assertScheduledCount(0)
        self.assertScheduledCount(1)

        self.assertScheduledCount(0)
        with transaction.atomic():
            task.delay()
            self.assertScheduledCount(0)
            with transaction.atomic():
                task.delay()
                self.assertScheduledCount(0)
            self.assertScheduledCount(0)
        self.assertScheduledCount(2)

        # Task delayed inside failed atomic transaction block is not scheduled.
        self.assertScheduledCount(0)
        with self.assertRaises(ValueError):
            with transaction.atomic():
                task.delay()
                raise ValueError('Testing')
        self.assertScheduledCount(0)

        self.assertScheduledCount(0)
        with transaction.atomic():
            task.delay()
            with self.assertRaises(ValueError):
                with transaction.atomic():
                    task.delay()
                    raise ValueError('Testing')
            self.assertScheduledCount(0)
        self.assertScheduledCount(1)
