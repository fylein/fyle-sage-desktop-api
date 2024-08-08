from apps.mappings.models import ImportLog
from apps.workspaces.models import ImportSetting
from apps.mappings.imports.modules.merchants import Merchant, disable_merchants
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute


def test_construct_fyle_payload(api_client, test_connection, mocker, create_temp_workspace, add_sage300_creds, add_fyle_credentials, add_merchant_mappings):
    merchant = Merchant(1, 'MERCHANT', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='MERCHANT')

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = merchant.get_auto_sync_permission()

    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == ['Direct Mail Campaign', 'Platform APIs']


def test_import_destination_attribute_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    workspace_id = 1

    merchant = Merchant(workspace_id, 'MERCHANT', None)

    mocker.patch(
        'apps.mappings.imports.modules.merchants.PlatformConnector'
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
    create_temp_workspace,
    add_merchant_mappings,
    add_import_settings
):
    merchant = Merchant(1, 'VENDOR', None)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')
    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {}

    # with code prepending
    merchant.use_code_in_naming = True
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR', code__isnull=False)
    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123 cre platform': '10065', '123 integrations cre': '10082'}


def test_construct_fyle_payload_with_code(
    db,
    create_temp_workspace,
    add_merchant_mappings,
    add_import_settings
):
    merchant = Merchant(1, 'VENDOR', None, True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='VENDOR')
    paginated_destination_attributes_without_duplicates = merchant.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = merchant.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = merchant.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == ['123 CRE Platform', '123 Integrations CRE']


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

    mock_platform = mocker.patch('apps.mappings.imports.modules.merchants.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.merchants, 'post')

    disable_merchants(workspace_id, merchants_to_disable)

    assert bulk_post_call.call_count == 1

    merchants_to_disable = {
        'destination_id': {
            'value': 'old_merchant_2',
            'updated_value': 'new_merchant',
            'code': 'old_merchant_code',
            'updated_code': 'new_merchant_code'
        }
    }

    disable_merchants(workspace_id, merchants_to_disable)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['VENDOR']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='MERCHANT',
        display_name='Merchant',
        value='old_merchant_code old_merchant',
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

    payload = ['old_merchant_code old_merchant']

    bulk_payload = disable_merchants(workspace_id, merchants_to_disable)
    assert bulk_payload[0] == payload[0]
