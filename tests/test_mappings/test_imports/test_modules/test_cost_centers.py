from apps.mappings.imports.modules.cost_centers import CostCenter
from fyle_accounting_mappings.models import DestinationAttribute
from .fixtures import data


def test_construct_fyle_payload(api_client, test_connection, mocker, create_temp_workspace, add_sage300_creds, add_fyle_credentials, add_cost_center_mappings):
    cost_center = CostCenter(1, 'COST_CENTER', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='COST_CENTER')

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = cost_center.get_auto_sync_permission()

    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == data['create_fyle_cost_center_payload_create_new_case']
