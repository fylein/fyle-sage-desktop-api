from fyle_integrations_imports.models import ImportLog
from apps.workspaces.models import ImportSetting
from fyle_integrations_imports.modules.merchants import Merchant, disable_merchants
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute


def test_construct_fyle_payload(api_client, test_connection, mocker, create_temp_workspace, add_sage300_creds, add_fyle_credentials, add_merchant_mappings):
    workspace_id = 1
    merchant = Merchant(workspace_id, 'MERCHANT', None, sdk_connection=mocker.Mock(), destination_sync_methods=['vendors'])

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='MERCHANT')

    existing_fyle_attributes_map = {}

    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
    )

    assert fyle_payload == ['Direct Mail Campaign', 'Platform APIs']


def test_import_destination_attribute_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    workspace_id = 1

    merchant = Merchant(workspace_id, 'MERCHANT', None, sdk_connection=mocker.Mock(), destination_sync_methods=['vendors'])

    mocker.patch(
        'fyle_integrations_imports.modules.merchants.PlatformConnector'
    )

    mocker.patch.object(
        merchant,
        'sync_expense_attributes',
        return_value=True
    )
    mocker.patch.object(
        merchant,
        'sync_destination_attributes',
        return_value=True
    )
    mocker.patch.object(
        merchant,
        'construct_payload_and_import_to_fyle',
        return_value=True
    )

    import_log = ImportLog(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        status='IN_PROGRESS',
        error_log={},
        total_batches_count=1,
        processed_batches_count=0,
        last_successful_run_at=None
    )

    merchant.import_destination_attribute_to_fyle(import_log)
    assert True


def test_get_existing_fyle_attributes(
    db,
    mocker,
    create_temp_workspace,
    add_merchant_mappings,
    add_import_settings
):
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None, sdk_connection=mocker.Mock(), destination_sync_methods=['vendors'])

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')
    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert len(existing_fyle_attributes_map) == 2

    # with code prepending
    merchant = Merchant(workspace_id, 'VENDOR', None, sdk_connection=mocker.Mock(), destination_sync_methods=['vendors'], prepend_code_to_name=True)
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR', code__isnull=False)
    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)

    values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    assert values == ['123: CRE Platform', '123: Integrations CRE']


def test_construct_fyle_payload_with_code(
    db,
    mocker,
    create_temp_workspace,
    add_merchant_mappings,
    add_import_settings
):
    workspace_id = 1
    merchant = Merchant(workspace_id, 'VENDOR', None, sdk_connection=mocker.Mock(), destination_sync_methods=['vendors'], prepend_code_to_name=True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')

    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)
    # already exists
    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
    )

    assert fyle_payload == [
        '123: CRE Platform',
        '123: Integrations CRE'
    ]

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
    )

    assert fyle_payload == ['123: CRE Platform', '123: Integrations CRE']


def test_disable_merchants(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_merchant_mappings,
    add_import_settings
):
    workspace_id = 1

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'old_merchant_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        display_name='Merchant',
        value='old_merchant',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('fyle_integrations_imports.modules.merchants.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.merchants, 'post')

    disable_merchants(workspace_id, merchants_to_disable, is_import_to_fyle_enabled=True)

    assert bulk_post_call.call_count == 1

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant_2',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'new_merchant_code'
        }
    }

    disable_merchants(workspace_id, merchants_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['VENDOR']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        display_name='Merchant',
        value='old_merchant_code: old_merchant',
        source_id='source_id_123',
        active=True
    )

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'old_merchant_code'
        }
    }

    payload = ['old_merchant_code: old_merchant']

    bulk_payload = disable_merchants(workspace_id, merchants_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_payload[0] == payload[0]
