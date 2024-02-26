from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField
from fyle_accounting_mappings.models import DestinationAttribute
from apps.mappings.models import ImportLog


def test_construct_custom_field_placeholder():
    expense_custom_fields = ExpenseCustomField(
        workspace_id=1,
        source_field="Vendor",
        destination_field="Vendor",
        sync_after="2024-01-01T00:00:00Z"
    )

    source_placeholder = "Source Placeholder"
    fyle_attribute = "Fyle Attribute"
    existing_attribute = {
        "placeholder": "Existing Placeholder"
    }

    expected_result = "Source Placeholder"
    result = expense_custom_fields.construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = None
    existing_attribute = {
        "placeholder": "Existing Placeholder"
    }

    expected_result = "Existing Placeholder"
    result = expense_custom_fields.construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = "Source Placeholder"
    existing_attribute = None

    expected_result = "Source Placeholder"
    result = expense_custom_fields.construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result

    source_placeholder = None
    existing_attribute = None

    expected_result = "Select Fyle Attribute"
    result = expense_custom_fields.construct_custom_field_placeholder(source_placeholder, fyle_attribute, existing_attribute)
    assert result == expected_result


def test_construct_fyle_expense_custom_field_payload(
    db,
    mocker,
    create_temp_workspace,
    add_expense_destination_attributes_2
):
    expense_custom_fields = ExpenseCustomField(
        workspace_id=1,
        source_field="CUSTOM",
        destination_field="CUSTOM",
        sync_after="2024-01-01T00:00:00Z"
    )

    sage300_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='CUSTOM')
    platform = mocker.patch('apps.mappings.imports.modules.expense_custom_fields.PlatformConnector')

    mocker.patch.object(
        platform.return_value.expense_custom_fields,
        'get_by_id',
        return_value={
            'id': '10081',
            'is_mandatory': False
        }
    )

    result = expense_custom_fields.construct_fyle_expense_custom_field_payload(sage300_attributes, platform)
    assert result['field_name'] == 'Custom'
    assert result['type'] == 'SELECT'
    assert result['is_enabled'] is True
    assert result['id'] == '10081'


def test_construct_payload_and_import_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_expense_destination_attributes_2
):
    expense_custom_fields = ExpenseCustomField(
        workspace_id=1,
        source_field="CUSTOM",
        destination_field="CUSTOM",
        sync_after="2024-01-01T00:00:00Z"
    )

    platform = mocker.patch('apps.mappings.imports.modules.expense_custom_fields.PlatformConnector')
    mocker.patch.object(
        expense_custom_fields,
        'post_to_fyle_and_sync',
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    expense_custom_fields.construct_payload_and_import_to_fyle(platform, import_log)

    import_log.refresh_from_db()
    assert import_log.total_batches_count == 1


def test_import_destination_attribute_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    expense_custom_fields = ExpenseCustomField(
        workspace_id=1,
        source_field="CUSTOM",
        destination_field="CUSTOM",
        sync_after="2024-01-01T00:00:00Z"
    )

    mocker.patch('apps.mappings.imports.modules.expense_custom_fields.PlatformConnector')

    mocker.patch.object(
        expense_custom_fields,
        'sync_destination_attributes',
    )
    mocker.patch.object(
        expense_custom_fields,
        'construct_fyle_expense_custom_field_payload',
    )
    mocker.patch.object(
        expense_custom_fields,
        'sync_expense_attributes',
    )
    mocker.patch.object(
        expense_custom_fields,
        'create_mappings',
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    expense_custom_fields.import_destination_attribute_to_fyle(import_log)
    assert True


def test_post_to_fyle_and_sync(
    db,
    mocker,
    create_temp_workspace
):
    expense_custom_fields = ExpenseCustomField(
        workspace_id=1,
        source_field="CUSTOM",
        destination_field="CUSTOM",
        sync_after="2024-01-01T00:00:00Z"
    )

    platform = mocker.patch('apps.mappings.imports.modules.expense_custom_fields.PlatformConnector')
    mocker.patch.object(
        platform.return_value,
        'post'
    )
    mocker.patch.object(
        platform.return_value,
        'bulk_post'
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    expense_custom_fields.post_to_fyle_and_sync(
        fyle_payload=[{
            'field_name': 'Custom',
            'type': 'SELECT',
            'is_enabled': True
        }],
        resource_class=platform.return_value,
        is_last_batch=True,
        import_log=import_log
    )

    platform.return_value.post.assert_called_once_with(
        [{
            'field_name': 'Custom',
            'type': 'SELECT',
            'is_enabled': True
        }]
    )
