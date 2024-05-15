from functools import wraps

from .models import TaskStatus


def handle_error(f, status: TaskStatus):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            status.error(str(e))
            raise

    return wrapper
