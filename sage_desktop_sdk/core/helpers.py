import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def retry(exceptions, tries=3, delay=2, backoff=2):
    """
    Decorator for retrying a function call with specified exceptions.

    :param exceptions: Exception or tuple of exceptions to catch and retry on.
    :param tries: Number of times to try (not retry) before giving up.
    :param delay: Initial delay between retries in seconds.
    :param backoff: Multiplier applied to delay between attempts.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.exception(f"{func.__name__} failed with {e}, retrying in {_delay} seconds...")
                    time.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator
