import logging
import threading
from functools import partial, wraps

from django.db import transaction

from cegs_portal.tasks.models import ThreadTask

logger = logging.getLogger("django.task")


def as_task(pass_task_id=False, description=None):
    """Wraps a function so it will run in a separate thread. A ThreadTask object
    will also be created so the task will be logged in the database and the
    state of the task can be checked.

    :param pass_id: Should the task id be passed to the wrapped function in the args list
    :type pass_id: bool
    :param description: A description of the task. This will be included in the DB and should be
        at most 140 chars.
    :type description: str
    """

    def as_task_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            def f_wrap(task_id, *args, **kwargs):
                logger.info(f"Task <{task_id}> started")

                try:
                    if pass_task_id:
                        args += (task_id,)
                    f(*args, **kwargs)
                except Exception as e:
                    ThreadTask.fail(task_id, str(e)[:1024])
                    logger.error(f"Task <{task_id}> failed")
                else:
                    ThreadTask.end(task_id)
                    logger.info(f"Task <{task_id}> ended")

            task = ThreadTask.new(description=description)
            task.save()

            def g(task_id):
                thread = threading.Thread(target=f_wrap, args=(task_id,) + args, kwargs=kwargs, daemon=False)
                thread.start()

            transaction.on_commit(partial(g, task.id))

            return task

        return wrapper

    return as_task_decorator
