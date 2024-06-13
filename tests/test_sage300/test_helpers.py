from datetime import datetime, timedelta, timezone
from apps.sage300.helpers import (
    check_interval_and_sync_dimension,
    sync_dimensions,
    disable_projects,
    update_and_disable_cost_code
)
from apps.workspaces.models import Workspace, Sage300Credential
from fyle_accounting_mappings.models import ExpenseAttribute
from apps.fyle.models import DependentFieldSetting
from apps.sage300.models import CostCategory


def test_check_interval_and_sync_dimension(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    mocker.patch('apps.sage300.helpers.sync_dimensions')

    workspace = Workspace.objects.get(id=workspace_id)
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

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

    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

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
    add_fyle_credentials
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project'
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

    mock_platform = mocker.patch('apps.sage300.helpers.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.projects, 'post_bulk')
    sync_call = mocker.patch.object(mock_platform.return_value.projects, 'sync')

    disable_cost_code_call = mocker.patch('apps.sage300.helpers.update_and_disable_cost_code')

    disable_projects(workspace_id, projects_to_disable)

    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 2
    disable_cost_code_call.assert_called_once()

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project_2',
            'updated_value': 'new_project'
        }
    }

    disable_projects(workspace_id, projects_to_disable)
    assert bulk_post_call.call_count == 1
    assert sync_call.call_count == 4
    disable_cost_code_call.call_count == 2


def test_update_and_disable_cost_code(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_dependent_field_setting,
    add_cost_category
):
    workspace_id = 1

    projects_to_disable = {
        'destination_id': {
            'value': 'old_project',
            'updated_value': 'new_project'
        }
    }

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

    mock_platform = mocker.patch('apps.sage300.helpers.PlatformConnector')
    mocker.patch.object(mock_platform.return_value.cost_centers, 'post_bulk')
    mocker.patch.object(mock_platform.return_value.cost_centers, 'sync')
    mocker.patch.object(mock_platform.return_value.dependent_fields, 'bulk_post_dependent_expense_field_values')

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform)

    updated_cost_category = CostCategory.objects.filter(workspace_id=workspace_id, job_id='destination_id').first()
    assert updated_cost_category.job_name == 'new_project'

    updated_cost_category.job_name = 'old_project'
    updated_cost_category.save()

    DependentFieldSetting.objects.get(workspace_id=workspace_id).delete()

    update_and_disable_cost_code(workspace_id, projects_to_disable, mock_platform)

    updated_cost_category = CostCategory.objects.filter(workspace_id=workspace_id, job_id='destination_id').first()
    assert updated_cost_category.job_name == 'old_project'
