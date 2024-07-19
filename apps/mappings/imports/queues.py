from django_q.tasks import Chain
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import ImportSetting
from apps.fyle.models import DependentFieldSetting
from apps.mappings.models import ImportLog
from apps.mappings.helpers import is_job_sync_allowed


def chain_import_fields_to_fyle(workspace_id):
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    dependent_field_settings = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    import_code_fields = import_settings.import_code_fields
    project_import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()

    # We'll only sync job when the time_difference > 30 minutes to avoid
    # any dependent field import issue due to timestamp on job name update
    is_sync_allowed = is_job_sync_allowed(project_import_log)

    custom_field_mapping_settings = []
    project_mapping = None

    for setting in mapping_settings:
        if setting.is_custom:
            custom_field_mapping_settings.append(setting)
        if setting.source_field == 'PROJECT':
            project_mapping = setting

    chain = Chain()

    if project_mapping and dependent_field_settings and is_sync_allowed:
        cost_code_import_log = ImportLog.create('COST_CODE', workspace_id)
        cost_category_import_log = ImportLog.create('COST_CATEGORY', workspace_id)
        chain.append('apps.mappings.tasks.sync_sage300_attributes', 'JOB', workspace_id)
        chain.append('apps.mappings.tasks.sync_sage300_attributes', 'COST_CODE', workspace_id, cost_code_import_log)
        chain.append('apps.mappings.tasks.sync_sage300_attributes', 'COST_CATEGORY', workspace_id, cost_category_import_log)

    if import_settings.import_categories:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'ACCOUNT',
            'CATEGORY',
            False,
            True if 'ACCOUNT' in import_code_fields else False
        )

    if import_settings.import_vendors_as_merchants:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'VENDOR',
            'MERCHANT'
        )

    for mapping_setting in mapping_settings:
        if mapping_setting.source_field in ['PROJECT', 'COST_CENTER']:
            chain.append(
                'apps.mappings.imports.tasks.trigger_import_via_schedule',
                workspace_id,
                mapping_setting.destination_field,
                mapping_setting.source_field,
                False,
                True if mapping_setting.destination_field in import_code_fields else False
            )

    for custom_fields_mapping_setting in custom_field_mapping_settings:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            custom_fields_mapping_setting.destination_field,
            custom_fields_mapping_setting.source_field,
            True,
            True if custom_fields_mapping_setting.destination_field in import_code_fields else False
        )

    if project_mapping and dependent_field_settings and is_sync_allowed:
        chain.append('apps.sage300.dependent_fields.import_dependent_fields_to_fyle', workspace_id)

    if chain.length() > 0:
        chain.run()
