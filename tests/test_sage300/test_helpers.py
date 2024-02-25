from datetime import datetime, timedelta, timezone
from apps.sage300.helpers import (
    check_interval_and_sync_dimension,
    sync_dimensions
)
from apps.workspaces.models import Workspace, Sage300Credential


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
            continue
