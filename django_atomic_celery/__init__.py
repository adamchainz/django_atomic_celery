import threading
from collections import defaultdict
from celery.task import task as base_task, Task
from django.dispatch import receiver
from django.db import DEFAULT_DB_ALIAS
from functools import partial
from django_atomic_signals import signals


_thread_data = threading.local()


def _get_task_queues():
    """Get the local task queues.

    The task queues are a :class:`dict` mapping database aliases to a
    :class:`list` of :class:`list` instances containing tasks for a given
    atomic block level.
    """

    return _thread_data.__dict__.setdefault('task_queues', defaultdict(list))


class PostTransactionTask(Task):
    """Task delayed until after the outermost atomic block is exited.

    If the atomic transaction block within which the task is scheduled is
    successful, ie. no exception is raised and the transaction is not rolled
    back, the task is promoted to the outside block. Otherwise, the task is
    discarded.

    When exiting the outside block, all surviving tasks are scheduled.
    """

    abstract = True

    @classmethod
    def original_apply_async(cls, *args, **kwargs):
        return super(PostTransactionTask, cls).apply_async(*args, **kwargs)

    @classmethod
    def apply_async(cls, *args, **kwargs):
        using = kwargs.get('using', DEFAULT_DB_ALIAS)
        task_queue_stack = _get_task_queues()[using]

        if task_queue_stack:
            task_queue_stack[-1].append((cls, args, kwargs))
        else:
            return cls.original_apply_async(*args, **kwargs)

    @classmethod
    def delay(cls, *args, **kwargs):
        return cls.apply_async(args, kwargs)


@receiver(signals.post_enter_atomic_block)
def _post_enter_atomic_block(signal,
                             sender,
                             using,
                             outermost,
                             savepoint,
                             **kwargs):
    if not savepoint:
        return

    using = using or DEFAULT_DB_ALIAS
    task_queue_stack = _get_task_queues()[using]

    if outermost:
        task_queue_stack[:] = []

    task_queue_stack.append([])


@receiver(signals.post_exit_atomic_block)
def _post_exit_atomic_block(signal,
                            sender,
                            using,
                            outermost,
                            savepoint,
                            successful,
                            **kwargs):
    if not savepoint:
        return

    using = using or DEFAULT_DB_ALIAS
    task_queue_stack = _get_task_queues()[using]

    if successful:
        if outermost:
            for cls, args, kwargs in task_queue_stack[0]:
                cls.original_apply_async(*args, **kwargs)

            task_queue_stack.pop()
        else:
            task_queue = task_queue_stack.pop()
            task_queue_stack[-1] += task_queue
    else:
        task_queue_stack.pop()


task = partial(base_task, base=PostTransactionTask)
