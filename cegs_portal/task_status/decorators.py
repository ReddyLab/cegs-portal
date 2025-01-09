import logging
from functools import wraps

from .models import TaskStatus

logger = logging.getLogger(__name__)


def handle_error(f, status: TaskStatus):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            status.error(str(e))
            logger.error(str(e))

    return wrapper
