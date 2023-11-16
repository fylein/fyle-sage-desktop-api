from apps.mappings.imports.modules.merchants import Merchant
from fyle_accounting_mappings.models import DestinationAttribute


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
