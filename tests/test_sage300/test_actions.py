import pytest
from datetime import datetime, timezone

from apps.sage300.actions import sync_dimensions, refresh_sage_dimension, get_sage_connector
from apps.workspaces.models import Workspace
from workers.helpers import WorkerActionEnum, RoutingKeyEnum


@pytest.mark.django_db
def test_get_sage_connector(db, add_sage300_creds):
    """Test get_sage_connector returns SageDesktopConnector"""
    from apps.sage300.utils import SageDesktopConnector

    connector = get_sage_connector(workspace_id=1)

    assert isinstance(connector, SageDesktopConnector)
    assert connector.workspace_id == 1


@pytest.mark.django_db
def test_sync_dimensions_first_sync(db, mocker, add_sage300_creds, create_temp_workspace):
    """Test sync_dimensions performs full sync when destination_synced_at is None"""
    workspace_id = 1

    # Ensure destination_synced_at is None
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.destination_synced_at = None
    workspace.save()

    # Mock connector methods
    mock_connector = mocker.Mock()
    mocker.patch('apps.sage300.actions.get_sage_connector', return_value=mock_connector)

    sync_dimensions(workspace_id)

    # Verify all sync methods were called
    mock_connector.sync_accounts.assert_called_once()
    mock_connector.sync_vendors.assert_called_once()
    mock_connector.sync_jobs.assert_called_once()
    mock_connector.sync_commitments.assert_called_once()
    mock_connector.sync_standard_categories.assert_called_once()
    mock_connector.sync_standard_cost_codes.assert_called_once()

    # Verify workspace was updated
    workspace.refresh_from_db()
    assert workspace.destination_synced_at is not None


@pytest.mark.django_db
def test_sync_dimensions_recent_sync(db, mocker, add_sage300_creds, create_temp_workspace):
    """Test sync_dimensions skips sync when recently synced (within 1 day)"""
    workspace_id = 1

    # Set destination_synced_at to recent time
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.destination_synced_at = datetime.now(timezone.utc)
    workspace.save()

    # Mock connector methods
    mock_connector = mocker.Mock()
    mocker.patch('apps.sage300.actions.get_sage_connector', return_value=mock_connector)

    sync_dimensions(workspace_id)

    # Verify sync methods were NOT called (recent sync)
    mock_connector.sync_accounts.assert_not_called()
    mock_connector.sync_vendors.assert_not_called()


@pytest.mark.django_db
def test_sync_dimensions_old_sync(db, mocker, add_sage300_creds, create_temp_workspace):
    """Test sync_dimensions performs sync when last sync was > 1 day ago"""
    from datetime import timedelta

    workspace_id = 1

    # Set destination_synced_at to 2 days ago
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.destination_synced_at = datetime.now(timezone.utc) - timedelta(days=2)
    workspace.save()

    # Mock connector methods
    mock_connector = mocker.Mock()
    mocker.patch('apps.sage300.actions.get_sage_connector', return_value=mock_connector)

    sync_dimensions(workspace_id)

    # Verify all sync methods were called
    mock_connector.sync_accounts.assert_called_once()
    mock_connector.sync_vendors.assert_called_once()
    mock_connector.sync_jobs.assert_called_once()


@pytest.mark.django_db
def test_refresh_sage_dimension_with_export_settings(
    db,
    mocker,
    add_sage300_creds,
    create_temp_workspace,
    add_export_settings
):
    """Test refresh_sage_dimension publishes to RabbitMQ when export settings exist"""
    workspace_id = 1

    mock_connector = mocker.Mock()
    mocker.patch('apps.sage300.actions.get_sage_connector', return_value=mock_connector)

    mock_publish = mocker.patch('apps.sage300.actions.publish_to_rabbitmq')

    refresh_sage_dimension(workspace_id)

    # Verify RabbitMQ publish was called
    assert mock_publish.called
    call_args = mock_publish.call_args
    payload = call_args[1]['payload']
    assert payload['action'] == WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE.value
    assert payload['workspace_id'] == workspace_id
    assert call_args[1]['routing_key'] == RoutingKeyEnum.IMPORT.value


@pytest.mark.django_db
def test_refresh_sage_dimension_without_export_settings(
    db,
    mocker,
    add_sage300_creds,
    create_temp_workspace
):
    """Test refresh_sage_dimension does not publish when no export settings"""
    workspace_id = 1

    mock_connector = mocker.Mock()
    mocker.patch('apps.sage300.actions.get_sage_connector', return_value=mock_connector)

    mock_publish = mocker.patch('apps.sage300.actions.publish_to_rabbitmq')

    refresh_sage_dimension(workspace_id)

    # Verify RabbitMQ publish was NOT called (no export settings)
    mock_publish.assert_not_called()
