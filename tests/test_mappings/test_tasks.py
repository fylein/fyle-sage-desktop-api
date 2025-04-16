from fyle_accounting_mappings.models import MappingSetting
from apps.mappings.tasks import sync_dependent_fields, sync_sage300_attributes, construct_tasks_and_chain_import_fields_to_fyle


def test_sync_sage300_attributes(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1

    mock_sage_connection = mocker.patch(
        'apps.mappings.tasks.SageDesktopConnector'
    )

    def test():
        pass

    attribute_types = {
        'JOB': 'jobs',
        'COST_CODE': 'cost_codes',
        'COST_CATEGORY': 'cost_categories',
        'ACCOUNT': 'accounts',
        'VENDOR': 'vendors',
        'COMMITMENT': 'commitments',
        'STANDARD_CATEGORY': 'standard_categories',
        'STANDARD_COST_CODE': 'standard_cost_codes'
    }

    for attribute_type, attribute_call in attribute_types.items():
        mocker.patch.object(mock_sage_connection.return_value, f'sync_{attribute_call}', return_value=test)
        sync_sage300_attributes(sage300_attribute_type=attribute_type, workspace_id=workspace_id)
        assert getattr(mock_sage_connection.return_value, f'sync_{attribute_call}').call_count == 1

    assert mock_sage_connection.call_count == len(attribute_types)


def test_sync_dependent_fields(db, mocker, create_temp_workspace, add_sage300_creds):
    """
    Test sync dependent fields
    """
    workspace_id = 1
    mocked_sync_fn = mocker.patch(
        'apps.mappings.tasks.sync_sage300_attributes'
    )

    sync_dependent_fields(workspace_id=workspace_id)
    assert mocked_sync_fn.call_count == 3


def test_construct_tasks_and_chain_import_fields_to_fyle(db, mocker, create_temp_workspace, add_import_settings, add_sage300_creds, add_dependent_field_setting):
    """
    Test construct tasks and chain import fields to fyle
    """
    workspace_id = 1
    MappingSetting.objects.create(
        source_field='PROJECT',
        destination_field='JOB',
        workspace_id=workspace_id,
        import_to_fyle=True,
        is_custom=False
    )

    mock_chain_fn = mocker.patch(
        'apps.mappings.tasks.chain_import_fields_to_fyle'
    )

    construct_tasks_and_chain_import_fields_to_fyle(workspace_id=workspace_id)

    assert mock_chain_fn.call_count == 1
