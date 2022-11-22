import logging
import threading
from functools import wraps

from cegs_portal.tasks.models import ThreadTask

logger = logging.getLogger("django.task")


def as_task(pass_id=False, description=None):
    def as_task_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            def f_wrap(*args, **kwargs):
                task = ThreadTask.new(description=description)
                task.save()
                logger.info(f"Task <{task}> started")
                try:
                    if pass_id:
                        args += (task.id,)
                    f(*args, **kwargs)
                except Exception as e:
                    ThreadTask.fail(task.id, str(e)[:1024])
                    logger.error(f"Task <{task}> failed")
                else:
                    ThreadTask.end(task.id)
                    logger.info(f"Task <{task}> ended")

            thread = threading.Thread(target=f_wrap, args=args, kwargs=kwargs, daemon=True)
            thread.start()

        return wrapper

    return as_task_decorator
