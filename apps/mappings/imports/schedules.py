from datetime import datetime
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting

from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import ImportSetting


def schedule_or_delete_dependent_field_tasks(workspace_id: int):
    """
    :param configuration: Workspace Configuration Instance
    :return: None
    """
    project_mapping = MappingSetting.objects.filter(
        source_field='PROJECT',
        workspace_id=workspace_id,
        import_to_fyle=True
    ).first()
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    if project_mapping and dependent_fields:
        start_datetime = datetime.now()
        Schedule.objects.update_or_create(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': start_datetime
            }
        )
    elif not (project_mapping and dependent_fields):
        Schedule.objects.filter(
            func='apps.mappings.tasks.auto_import_and_map_fyle_fields',
            args='{}'.format(workspace_id)
        ).delete()


def schedule_or_delete_fyle_import_tasks(import_settings: ImportSetting, mapping_setting_instance: MappingSetting = None):
    """
    Schedule or delete Fyle import tasks based on the import settingss.
    :param import_settingss: Workspace ImportSetting Instance
    :param instance: Mapping Setting Instance
    :return: None
    """
    task_to_be_scheduled = None
    # Check if there is a task to be scheduled
    if mapping_setting_instance and mapping_setting_instance.import_to_fyle:
        task_to_be_scheduled = mapping_setting_instance

    if task_to_be_scheduled or import_settings.import_categories:
        Schedule.objects.update_or_create(
            func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
            args='{}'.format(import_settings.workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
        return

    import_fields_count = MappingSetting.objects.filter(
        import_to_fyle=True,
        workspace_id=import_settings.workspace_id,
        source_field__in=['CATEGORY', 'PROJECT', 'COST_CENTER']
    ).count()

    custom_field_import_fields_count = MappingSetting.objects.filter(
        import_to_fyle=True,
        workspace_id=import_settings.workspace_id,
        is_custom=True
    ).count()

    # If the import fields count is 0, delete the schedule
    if import_fields_count == 0 and custom_field_import_fields_count == 0:
        Schedule.objects.filter(
            func='apps.mappings.imports.queues.chain_import_fields_to_fyle',
            args='{}'.format(import_settings.workspace_id)
        ).delete()

    # Schedule or delete dependent field tasks
    schedule_or_delete_dependent_field_tasks(import_settings.workspace_id)
