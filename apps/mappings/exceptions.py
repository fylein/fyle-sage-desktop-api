import logging
import traceback

from sage_desktop_sdk.exceptions import InvalidUserCredentials
from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError,
    RetryException
)
from apps.mappings.models import ImportLog
from apps.workspaces.models import Sage300Credential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_import_exceptions(func):
    def new_fn(expense_attribute_instance, *args):
        import_log: ImportLog = args[0]
        workspace_id = import_log.workspace_id
        attribute_type = import_log.attribute_type
        error = {
            'task': 'Import {0} to Fyle and Auto Create Mappings'.format(attribute_type),
            'workspace_id': workspace_id,
            'message': None,
            'response': None
        }
        try:
            return func(expense_attribute_instance, *args)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            import_log.status = 'FAILED'

        except (Sage300Credential.DoesNotExist, InvalidUserCredentials):
            error['message'] = 'Invalid Token or Sage 300 credentials does not exist workspace_id - {0}'.format(workspace_id)
            error['alert'] = False
            import_log.status = 'FAILED'

        except FyleInvalidTokenError:
            error['message'] = 'Invalid Token for fyle'
            error['alert'] = False
            import_log.status = 'FAILED'

        except RetryException:
            error['message'] = 'Fyle Retry Exception occured'
            import_log.status = 'FATAL'
            error['alert'] = False

        except InternalServerError:
            error['message'] = 'Internal server error while importing to Fyle'
            error['alert'] = True
            import_log.status = 'FAILED'

        except Exception:
            response = traceback.format_exc()
            error['message'] = 'Something went wrong'
            error['response'] = response
            error['alert'] = False
            import_log.status = 'FATAL'

        if error['alert']:
            logger.error(error)
        else:
            logger.info(error)

        import_log.error_log = error
        import_log.save()

    return new_fn


def handle_import_exceptions_v2(func):
    def new_fn(*args, **kwargs):
        import_log: ImportLog = args[0]
        workspace_id = import_log.workspace_id
        attribute_type = import_log.attribute_type
        error = {
            'task': 'Import {0} to Fyle and Auto Create Mappings'.format(attribute_type),
            'workspace_id': workspace_id,
            'message': None,
            'response': None
        }
        try:
            return func(*args, **kwargs)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            import_log.status = 'FAILED'

        except (Sage300Credential.DoesNotExist, InvalidUserCredentials):
            error['message'] = 'Invalid Token or Sage 300 credentials does not exist workspace_id - {0}'.format(workspace_id)
            error['alert'] = False
            import_log.status = 'FAILED'

        except FyleInvalidTokenError:
            error['message'] = 'Invalid Token for fyle'
            error['alert'] = False
            import_log.status = 'FAILED'

        except RetryException:
            error['message'] = 'Fyle Retry Exception occured'
            import_log.status = 'FATAL'
            error['alert'] = False

        except InternalServerError:
            error['message'] = 'Internal server error while importing to Fyle'
            error['alert'] = True
            import_log.status = 'FAILED'

        except Exception:
            response = traceback.format_exc()
            error['message'] = 'Something went wrong'
            error['response'] = response
            error['alert'] = False
            import_log.status = 'FATAL'

        if error['alert']:
            logger.error(error)
        else:
            logger.info(error)

        import_log.error_log = error
        import_log.save()

    return new_fn
