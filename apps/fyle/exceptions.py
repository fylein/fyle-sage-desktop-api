import logging
import traceback
from functools import wraps

from fyle.platform.exceptions import NoPrivilegeError, RetryException

from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FyleCredential.DoesNotExist:
            logger.info('Fyle credentials not found %s', args[0])  # args[1] is workspace_id
            args[1].detail = {'message': 'Fyle credentials do not exist in workspace'}
            args[1].status = 'FAILED'
            args[1].save()

        except NoPrivilegeError:
            logger.info('Invalid Fyle Credentials / Admin is disabled')
            args[1].detail = {'message': 'Invalid Fyle Credentials / Admin is disabled'}
            args[1].status = 'FAILED'
            args[1].save()

        except RetryException:
            logger.info('Fyle Retry Exception occured')
            args[1].detail = {'message': 'Fyle Retry Exception occured'}
            args[1].status = 'FATAL'
            args[1].save()

        except Exception:
            error = traceback.format_exc()
            args[1].detail = {'error': error}
            args[1].status = 'FATAL'
            args[1].save()
            logger.exception('Something unexpected happened workspace_id: %s %s', args[0], args[1].detail)

    return wrapper
