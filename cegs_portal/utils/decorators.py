from functools import wraps

from django.conf import settings


def skip_receiver_in_testing(f):
    """
    Wraps a signal receiver so that it won't be run during testing.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not settings.TESTING:
            return f(*args, **kwargs)

    return wrapper
