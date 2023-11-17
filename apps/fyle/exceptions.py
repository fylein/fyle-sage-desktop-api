import logging
import traceback
from functools import wraps

from fyle.platform.exceptions import NoPrivilegeError

from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FyleCredential.DoesNotExist:
            logger.info('Fyle credentials not found %s', args[1])  # args[1] is workspace_id
            args[2].detail = {'message': 'Fyle credentials do not exist in workspace'}
            args[2].status = 'FAILED'
            args[2].save()

        except NoPrivilegeError:
            logger.info('Invalid Fyle Credentials / Admin is disabled')
            args[2].detail = {'message': 'Invalid Fyle Credentials / Admin is disabled'}
            args[2].status = 'FAILED'
            args[2].save()

        except Exception:
            error = traceback.format_exc()
            args[2].detail = {'error': error}
            args[2].status = 'FATAL'
            args[2].save()
            logger.exception('Something unexpected happened workspace_id: %s %s', args[1], args[2].detail)

    return wrapper
