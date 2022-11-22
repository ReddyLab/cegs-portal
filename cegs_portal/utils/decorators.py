from functools import wraps

from django.conf import settings


def skip_in_testing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not settings.TESTING:
            return f(*args, **kwargs)

    return wrapper
