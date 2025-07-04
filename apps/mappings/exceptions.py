import logging
import traceback
from django.utils.module_loading import import_string

from fyle.platform.exceptions import (
    WrongParamsError,
    InvalidTokenError as FyleInvalidTokenError,
    InternalServerError,
    RetryException
)

from sage_desktop_sdk.exceptions import InvalidUserCredentials
from fyle_integrations_imports.models import ImportLog
from apps.workspaces.models import Sage300Credential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_import_exceptions_v2(func):
    def new_fn(expense_attribute_instance, *args, **kwargs):
        import_log = None
        if isinstance(expense_attribute_instance, ImportLog):
            import_log: ImportLog = expense_attribute_instance
        else:
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
            return func(expense_attribute_instance, *args, **kwargs)
        except WrongParamsError as exception:
            error['message'] = exception.message
            error['response'] = exception.response
            error['alert'] = True
            import_log.status = 'FAILED'

        except Sage300Credential.DoesNotExist:
            error['message'] = 'Sage 300 credentials does not exist workspace_id - {0}'.format(workspace_id)
            error['alert'] = False
            import_log.status = 'FAILED'

        except InvalidUserCredentials:
            invalidate_sage300_credentials = import_string('sage_desktop_api.utils.invalidate_sage300_credentials')
            invalidate_sage300_credentials(workspace_id)
            error['message'] = 'Invalid Sage 300 Token Error for workspace_id - {0}'.format(workspace_id)
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
