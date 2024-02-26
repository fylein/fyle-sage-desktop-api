from apps.mappings.imports.modules.merchants import Merchant
from fyle_accounting_mappings.models import DestinationAttribute
from apps.mappings.models import ImportLog


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
