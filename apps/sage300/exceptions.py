
import logging
import traceback

from sage_desktop_api.exceptions import BulkError
from apps.workspaces.models import FyleCredential, Sage300Credential
from sage_desktop_sdk.exceptions.hh2_exceptions import WrongParamsError
from apps.accounting_exports.models import AccountingExport
from apps.accounting_exports.models import Error
from apps.sage300.actions import update_last_export_details


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_sage300_error(exception, accounting_export: AccountingExport, export_type: str):
    logger.info(exception.response)

    sage300_error = exception.response
    error_msg = 'Failed to create {0}'.format(export_type)

    Error.objects.update_or_create(workspace_id=accounting_export.workspace_id, accounting_export=accounting_export, defaults={'error_title': error_msg, 'type': 'SAGE300_ERROR', 'error_detail': sage300_error, 'is_resolved': False})

    accounting_export.status = 'FAILED'
    accounting_export.detail = None
    accounting_export.sage300_errors = sage300_error
    accounting_export.save()


def handle_sage300_exceptions():
    def decorator(func):
        def new_fn(*args):

            accounting_export = args[0]

            try:
                return func(*args)
            except (FyleCredential.DoesNotExist):
                logger.info('Fyle credentials not found %s', accounting_export.workspace_id)
                accounting_export.detail = {'message': 'Fyle credentials do not exist in workspace'}
                accounting_export.status = 'FAILED'

                accounting_export.save()

            except Sage300Credential.DoesNotExist:
                logger.info('Sage300 Account not connected / token expired for workspace_id %s / accounting export %s', accounting_export.workspace_id, accounting_export.id)
                detail = {'accounting_export_id': accounting_export.id, 'message': 'Sage300 Account not connected / token expired'}
                accounting_export.status = 'FAILED'
                accounting_export.detail = detail

                accounting_export.save()

            except WrongParamsError as exception:
                handle_sage300_error(exception, accounting_export, 'Purchase Invoice')

            except BulkError as exception:
                logger.info(exception.response)
                detail = exception.response
                accounting_export.status = 'FAILED'
                accounting_export.detail = detail

                accounting_export.save()

            except Exception as error:
                error = traceback.format_exc()
                accounting_export.detail = {'error': error}
                accounting_export.status = 'FATAL'

                accounting_export.save()
                logger.error('Something unexpected happened workspace_id: %s %s', accounting_export.workspace_id, accounting_export.detail)

            update_last_export_details(accounting_export.workspace_id)

        return new_fn

    return decorator
