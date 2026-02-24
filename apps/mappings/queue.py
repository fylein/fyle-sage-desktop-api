import logging

from fyle_accounting_mappings.models import MappingSetting
from fyle_integrations_imports.models import ImportLog
from fyle_integrations_imports.dataclasses import TaskSetting
from fyle_integrations_imports.queues import chain_import_fields_to_fyle

from apps.mappings.constants import SYNC_METHODS
from apps.mappings.helpers import is_job_sync_allowed
from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import Sage300Credential, ImportSetting

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def initiate_import_to_fyle(workspace_id: int) -> None:
    """
    Construct tasks and chain import fields to fyle
    :param workspace_id: Workspace ID
    :return: None
    """
    try:
        mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
        import_settings = ImportSetting.objects.filter(workspace_id=workspace_id).first()

        if not import_settings:
            logger.warning(f'Import settings not found for workspace {workspace_id}, skipping import')
            return

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

        chain_import_fields_to_fyle(workspace_id, task_settings, run_in_rabbitmq_worker=True)
    except Exception as e:
        logger.error(f'Error initiating import to Fyle for workspace {workspace_id}: {e}')
        raise
