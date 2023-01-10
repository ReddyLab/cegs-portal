import logging
import threading
from functools import wraps

from cegs_portal.tasks.models import ThreadTask

logger = logging.getLogger("django.task")


def as_task(pass_task=False, description=None):
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
            def f_wrap(task, *args, **kwargs):
                logger.info(f"Task <{task}> started")
                try:
                    if pass_task:
                        args += (task,)
                    f(*args, **kwargs)
                except Exception as e:
                    task.fail(str(e)[:1024])
                    logger.error(f"Task <{task}> failed")
                else:
                    task.end()
                    logger.info(f"Task <{task}> ended")

            task = ThreadTask.new(description=description)
            task.save()

            thread = threading.Thread(target=f_wrap, args=(task,) + args, kwargs=kwargs, daemon=True)
            thread.start()

            return task

        return wrapper

    return as_task_decorator
