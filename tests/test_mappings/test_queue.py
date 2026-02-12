import pytest
from fyle_accounting_mappings.models import MappingSetting

from apps.mappings.queue import initiate_import_to_fyle
from apps.workspaces.models import ImportSetting


@pytest.mark.django_db
def test_initiate_import_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_import_settings
):
    """Test initiate_import_to_fyle builds task settings and calls chain_import_fields_to_fyle"""
    workspace_id = 1

    mock_chain = mocker.patch('apps.mappings.queue.chain_import_fields_to_fyle')

    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='PROJECT',
        destination_field='JOB',
        import_to_fyle=True
    )

    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='COST_CENTER',
        destination_field='COMMITMENT',
        import_to_fyle=True
    )

    initiate_import_to_fyle(workspace_id)

    # Verify chain_import_fields_to_fyle was called with run_in_rabbitmq_worker=True
    mock_chain.assert_called_once()
    args, kwargs = mock_chain.call_args

    assert args[0] == workspace_id
    assert 'run_in_rabbitmq_worker' in kwargs
    assert kwargs['run_in_rabbitmq_worker'] is True

    # Verify task_settings structure
    task_settings = args[1]
    assert 'credentials' in task_settings
    assert 'sdk_connection_string' in task_settings
    assert task_settings['sdk_connection_string'] == 'apps.sage300.utils.SageDesktopConnector'


@pytest.mark.django_db
def test_initiate_import_to_fyle_with_categories(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    """Test initiate_import_to_fyle with category import enabled"""
    workspace_id = 1

    ImportSetting.objects.create(
        workspace_id=workspace_id,
        import_categories=True,
        import_code_fields=['ACCOUNT']
    )

    mock_chain = mocker.patch('apps.mappings.queue.chain_import_fields_to_fyle')

    initiate_import_to_fyle(workspace_id)

    mock_chain.assert_called_once()
    task_settings = mock_chain.call_args[0][1]

    assert task_settings['import_categories'] is not None
    assert task_settings['import_categories']['destination_field'] == 'ACCOUNT'
    assert task_settings['import_categories']['prepend_code_to_name'] is True


@pytest.mark.django_db
def test_initiate_import_to_fyle_with_vendors(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    """Test initiate_import_to_fyle with vendor import enabled"""
    workspace_id = 1

    ImportSetting.objects.create(
        workspace_id=workspace_id,
        import_vendors_as_merchants=True,
        import_code_fields=['VENDOR']
    )

    mock_chain = mocker.patch('apps.mappings.queue.chain_import_fields_to_fyle')

    initiate_import_to_fyle(workspace_id)

    mock_chain.assert_called_once()
    task_settings = mock_chain.call_args[0][1]

    assert task_settings['import_vendors_as_merchants'] is not None
    assert task_settings['import_vendors_as_merchants']['destination_field'] == 'VENDOR'
    assert task_settings['import_vendors_as_merchants']['prepend_code_to_name'] is True
