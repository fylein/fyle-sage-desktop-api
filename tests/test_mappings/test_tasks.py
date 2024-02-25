from apps.mappings.tasks import sync_sage300_attributes


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
