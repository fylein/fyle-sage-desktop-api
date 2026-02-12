import logging
from django.utils.module_loading import import_string

from fyle_integrations_imports.models import ImportLog

from apps.sage300.utils import SageDesktopConnector
from apps.workspaces.models import Sage300Credential
from sage_desktop_sdk.exceptions import InvalidUserCredentials
from workers.helpers import publish_to_rabbitmq, RoutingKeyEnum, WorkerActionEnum

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def sync_sage300_attributes(sage300_attribute_type: str, workspace_id: int, import_log: ImportLog = None):
    sage300_credentials: Sage300Credential = Sage300Credential.get_active_sage300_credentials(workspace_id)

    sage300_connection = SageDesktopConnector(
        credentials_object=sage300_credentials,
        workspace_id=workspace_id
    )

    sync_functions = {
        'JOB': sage300_connection.sync_jobs,
        'COST_CODE': lambda:sage300_connection.sync_cost_codes(import_log),
        'COST_CATEGORY': lambda:sage300_connection.sync_cost_categories(import_log),
        'ACCOUNT': sage300_connection.sync_accounts,
        'VENDOR': sage300_connection.sync_vendors,
        'COMMITMENT': sage300_connection.sync_commitments,
        'STANDARD_CATEGORY': sage300_connection.sync_standard_categories,
        'STANDARD_COST_CODE': sage300_connection.sync_standard_cost_codes,
    }

    sync_function = sync_functions[sage300_attribute_type]
    sync_function()


def construct_tasks_and_chain_import_fields_to_fyle(workspace_id: int) -> None:
    """
    Initiate the Import of dimensions to Fyle
    :param workspace_id: Workspace Id
    :return: None
    """
    payload = {
        'workspace_id': workspace_id,
        'action': WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE.value,
        'data': {
            'workspace_id': workspace_id
        }
    }
    publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)


def sync_dependent_fields(workspace_id: int) -> None:
    """
    sync_dependent_fields
    :param workspace_id: Workspace ID
    :return: None
    """
    try:
        cost_code_import_log = ImportLog.update_or_create_in_progress_import_log('COST_CODE', workspace_id)
        cost_category_import_log = ImportLog.update_or_create_in_progress_import_log('COST_CATEGORY', workspace_id)
        sync_sage300_attributes('JOB', workspace_id)
        sync_sage300_attributes('COST_CODE', workspace_id, cost_code_import_log)
        sync_sage300_attributes('COST_CATEGORY', workspace_id, cost_category_import_log)

    except Sage300Credential.DoesNotExist:
        logger.info('Sage credentials not found in workspace')
        return

    except InvalidUserCredentials:
        invalidate_sage300_credentials = import_string('sage_desktop_api.utils.invalidate_sage300_credentials')
        invalidate_sage300_credentials(workspace_id)
        return
