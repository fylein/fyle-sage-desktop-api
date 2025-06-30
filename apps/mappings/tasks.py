from fyle_accounting_mappings.models import MappingSetting
from django.utils.module_loading import import_string

from fyle_integrations_imports.models import ImportLog
from fyle_integrations_imports.dataclasses import TaskSetting
from fyle_integrations_imports.queues import chain_import_fields_to_fyle

from apps.mappings.constants import SYNC_METHODS
from apps.sage300.utils import SageDesktopConnector
from apps.mappings.helpers import is_job_sync_allowed
from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import Sage300Credential, ImportSetting
from sage_desktop_sdk.exceptions import InvalidUserCredentials


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
    Construct tasks and chain import fields to fyle
    :param workspace_id: Workspace ID
    :return: None
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    dependent_field_settings = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()
    project_mapping = mapping_settings.filter(source_field='PROJECT', destination_field='JOB', import_to_fyle=True).first()
    project_import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    is_sync_allowed = is_job_sync_allowed(project_import_log)
    credentials = Sage300Credential.get_active_sage300_credentials(workspace_id)

    task_settings: TaskSetting = {
        'import_tax': None,
        'import_vendors_as_merchants': None,
        'import_categories': None,
        'import_items': None,
        'mapping_settings': [],
        'credentials': credentials,
        'sdk_connection_string': 'apps.sage300.utils.SageDesktopConnector',
        'custom_properties': None,
        'import_dependent_fields': None
    }

    if import_settings.import_categories:
        task_settings['import_categories'] = {
            'destination_field': 'ACCOUNT',
            'destination_sync_methods': ['accounts'],
            'is_auto_sync_enabled': True,
            'is_3d_mapping': False,
            'charts_of_accounts': [],
            'prepend_code_to_name': True if 'ACCOUNT' in import_settings.import_code_fields else False,
            'import_without_destination_id': True,
            'use_mapping_table': False
        }

    if import_settings.import_vendors_as_merchants:
        task_settings['import_vendors_as_merchants'] = {
            'destination_field': 'VENDOR',
            'destination_sync_methods': ['vendors'],
            'is_auto_sync_enabled': True,
            'is_3d_mapping': False,
            'prepend_code_to_name': True if 'VENDOR' in import_settings.import_code_fields else False,
        }

    for setting in mapping_settings:
        if (
            setting.source_field in ['PROJECT', 'COST_CENTER']
            or setting.is_custom
        ):
            task_settings['mapping_settings'].append({
                'source_field': setting.source_field,
                'destination_field': setting.destination_field,
                'destination_sync_methods': [SYNC_METHODS[setting.destination_field]],
                'is_auto_sync_enabled': True,
                'is_custom': setting.is_custom,
                'import_without_destination_id': True,
                'prepend_code_to_name': True if setting.destination_field in import_settings.import_code_fields else False
            })

    if project_mapping and is_sync_allowed and dependent_field_settings and dependent_field_settings.is_import_enabled:
        task_settings['custom_properties'] = {
            'func': 'apps.mappings.tasks.sync_dependent_fields',
            'args': {
                'workspace_id': workspace_id
            }
        }

        task_settings['import_dependent_fields'] = {
            'func': 'apps.sage300.dependent_fields.import_dependent_fields_to_fyle',
            'args': {
                'workspace_id': workspace_id
            }
        }

    chain_import_fields_to_fyle(workspace_id, task_settings)


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
