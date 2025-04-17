from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import ImportSetting
from apps.mappings.schedules import schedule_or_delete_fyle_import_tasks


def test_schedule_projects_creation(
    test_connection,
    create_temp_workspace,
    add_sage300_creds,
    add_fyle_credentials,
    add_import_settings,
    create_project_mapping_settings
):
    workspace_id = 1

    # Test schedule projects creation
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = True
    import_setting.import_vendors_as_merchants = True
    import_setting.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='PROJECT', destination_field='PROJECT', import_to_fyle=True).first()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'

    # Test delete schedule projects creation
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = False
    import_setting.import_vendors_as_merchants = False
    import_setting.save()

    mapping_setting = MappingSetting.objects.filter(workspace_id=workspace_id, source_field='PROJECT', destination_field='PROJECT', import_to_fyle=True).first()
    mapping_setting.import_to_fyle = False
    mapping_setting.save()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None

    # Test schedule categories creation adding the new schedule and not adding the old one
    import_setting = ImportSetting.objects.get(workspace_id=workspace_id)
    import_setting.import_categories = True
    import_setting.import_vendors_as_merchants = False
    import_setting.save()

    schedule_or_delete_fyle_import_tasks(import_setting, mapping_setting)

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'

    schedule = Schedule.objects.filter(
        func='apps.mappings.imports.auto_import_and_map_fyle_fields',
        args='{}'.format(workspace_id),
    ).first()

    assert schedule == None
