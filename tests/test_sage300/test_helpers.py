from datetime import datetime, timedelta, timezone

from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute

from apps.fyle.models import DependentFieldSetting
from apps.sage300.dependent_fields import update_and_disable_cost_code
from apps.sage300.helpers import check_interval_and_sync_dimension, sync_dimensions
from apps.sage300.models import CostCategory
from apps.workspaces.models import ImportSetting, Sage300Credential, Workspace
from fyle_integrations_imports.modules.projects import disable_projects
from tests.helper import dict_compare_keys


def test_check_interval_and_sync_dimension(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    mocker.patch('apps.sage300.helpers.sync_dimensions')

    workspace = Workspace.objects.get(id=workspace_id)
    sage_creds = Sage300Credential.get_active_sage300_credentials(workspace_id)

    workspace.destination_synced_at = datetime.now(timezone.utc) - timedelta(days=2)

    result = check_interval_and_sync_dimension(
        workspace=workspace,
        sage300_credential=sage_creds
    )

    assert result == True

    workspace.destination_synced_at = datetime.now(timezone.utc)
    workspace.save()

    result = check_interval_and_sync_dimension(
        workspace=workspace,
        sage300_credential=sage_creds
    )

    assert result == False


def test_sync_dimensions(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    def test():
        pass

    workspace_id = 1

    sage_creds = Sage300Credential.get_active_sage300_credentials(workspace_id)

    mock_sage_connector = mocker.patch('apps.sage300.utils.SageDesktopConnector')

    dimensions = ['standard_categories', 'standard_cost_codes',  'cost_codes', 'cost_categories']

    for dimension in dimensions:
        mocker.patch.object(
            mock_sage_connector.return_value,
            f'sync_{dimension}',
            return_value=test
        )

        sync_dimensions(
            sage300_credential=sage_creds,
            workspace_id=workspace_id
        )

    assert True

    for dimension in dimensions:
        mocker.patch.object(
            mock_sage_connector.return_value,
            f'sync_{dimension}',
            side_effect=Exception('Error')
        )

        try:
            sync_dimensions(
                sage300_credential=sage_creds,
                workspace_id=workspace_id
            )
        except Exception as e:
            assert str(e) == 'Error'


def test_disable_projects(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_project_mappings,
    add_import_settings
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'old_project_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project',
        source_id='source_id',
        active=True
    )

    DestinationAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project',
        destination_id='old_project_code',
        code='old_project_code'
    )

    mock_platform = mocker.patch('fyle_integrations_imports.modules.projects.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.projects, 'post_bulk')
    sync_call = mocker.patch.object(mock_platform.return_value.projects, 'sync')

    disable_cost_code_call = mocker.patch('apps.sage300.dependent_fields.update_and_disable_cost_code')

    disable_projects(workspace_id, projects_to_disable, is_import_to_fyle_enabled=True, attribute_type='PROJECT')

    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 2
    disable_cost_code_call.call_count == 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project_2',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'new_project_code'
        }
    }

    disable_projects(workspace_id, projects_to_disable, is_import_to_fyle_enabled=True, attribute_type='PROJECT')
    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 3
    disable_cost_code_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['JOB']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project_code: old_project',
        source_id='source_id_123',
        active=True
    )

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'old_project_code',
            'updated_code': 'old_project_code'
        }
    }

    payload = [{
        'name': 'old_project_code: old_project',
        'code': None,
        'description': 'Project - {0}, Id - {1}'.format(
            'old_project_code: old_project',
            'destination_id'
        ),
        'is_enabled': False,
        'id': 'source_id_123'
    }]

    response_payload = disable_projects(workspace_id, projects_to_disable, is_import_to_fyle_enabled=True, attribute_type='PROJECT')

    assert dict_compare_keys(response_payload, payload) == [], 'Response payload does not match expected payload'


def test_update_and_disable_cost_code(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_dependent_field_setting,
    add_cost_category,
    add_import_settings
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project',
            'code': 'new_project_code',
            'updated_code': 'new_project_code'
        }
    }

    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    use_code_in_naming = False
    if 'JOB' in import_settings.import_code_fields:
        use_code_in_naming = True

    cost_category = CostCategory.objects.filter(workspace_id=workspace_id).first()
    cost_category.job_name = 'old_project'
    cost_category.job_id = 'destination_id'
    cost_category.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('fyle_integrations_imports.modules.projects.PlatformConnector')
    mocker.patch.object(mock_platform.return_value.projects, 'post_bulk')
    mocker.patch.object(mock_platform.return_value.projects, 'sync')
    mocker.patch.object(mock_platform.return_value.dependent_fields, 'bulk_post_dependent_expense_field_values')

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)

    updated_cost_category = CostCategory.objects.filter(workspace_id=workspace_id, job_id='destination_id').first()
    assert updated_cost_category.job_name == 'new_project'

    # Test with code in naming
    use_code_in_naming = True

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='PROJECT',
        display_name='Project',
        value='old_project_code old_project',
        source_id='source_id_123',
        active=True
    )

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)
    assert updated_cost_category.job_name == 'new_project'
    assert updated_cost_category.job_code == 'new_project_code'

    # Delete dependent field setting
    updated_cost_category.job_name = 'old_project'
    updated_cost_category.save()

    DependentFieldSetting.objects.get(workspace_id=workspace_id).delete()

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform, use_code_in_naming)

    updated_cost_category = CostCategory.objects.filter(workspace_id=workspace_id, job_id='destination_id').first()
    assert updated_cost_category.job_name == 'old_project'
