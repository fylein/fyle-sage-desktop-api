from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute, MappingSetting
from fyle_integrations_imports.modules.cost_centers import CostCenter, disable_cost_centers
from apps.workspaces.models import ImportSetting
from .fixtures import data


def test_construct_fyle_payload(api_client, test_connection, mocker, create_temp_workspace, add_sage300_creds, add_fyle_credentials, add_cost_center_mappings):
    cost_center = CostCenter(1, 'COST_CENTER', None, sdk_connection=mocker.Mock(), destination_sync_methods=['jobs'], is_auto_sync_enabled=True)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='COST_CENTER')

    existing_fyle_attributes_map = {}

    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map
    )

    assert fyle_payload == data['create_fyle_cost_center_payload_create_new_case']


def test_get_existing_fyle_attributes(
    db,
    mocker,
    create_temp_workspace,
    add_cost_center_mappings,
    add_import_settings
):
    cost_center = CostCenter(1, 'JOB', None, sdk_connection=mocker.Mock(), destination_sync_methods=['jobs'])

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='JOB')
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {}

    # with code prepending
    cost_center = CostCenter(1, 'JOB', None, sdk_connection=mocker.Mock(), destination_sync_methods=['jobs'], prepend_code_to_name=True)
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='JOB', code__isnull=False)
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123: cre platform': '10065', '123: integrations cre': '10082'}


def test_construct_fyle_payload_with_code(
    db,
    mocker,
    create_temp_workspace,
    add_cost_center_mappings,
    add_import_settings
):
    cost_center = CostCenter(1, 'JOB', None, sdk_connection=mocker.Mock(), destination_sync_methods=['jobs'], prepend_code_to_name=True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='JOB')
    paginated_destination_attributes_without_duplicates = cost_center.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = cost_center.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = cost_center.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
    )

    assert fyle_payload == data["create_fyle_cost_center_payload_with_code_create_new_case"]


def test_disable_cost_centers(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_cost_center_mappings,
    add_import_settings
):
    workspace_id = 1

    MappingSetting.objects.create(
        workspace_id=workspace_id,
        source_field='COST_CENTER',
        destination_field='JOB',
        import_to_fyle=True,
        is_custom=False
    )

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'old_cost_center_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CENTER',
        display_name='CostCenter',
        value='old_cost_center',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('fyle_integrations_imports.modules.cost_centers.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.cost_centers, 'post_bulk')

    disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)

    assert bulk_post_call.call_count == 1

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center_2',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'new_cost_center_code'
        }
    }

    disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['JOB']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='COST_CENTER',
        display_name='CostCenter',
        value='old_cost_center_code: old_cost_center',
        source_id='source_id_123',
        active=True
    )

    cost_centers_to_disable = {
        'destination_id': {
            'value': 'old_cost_center',
            'updated_value': 'new_cost_center',
            'code': 'old_cost_center_code',
            'updated_code': 'old_cost_center_code'
        }
    }

    payload = [
        {
            'name': 'old_cost_center_code: old_cost_center',
            'code': 'destination_id',
            'is_enabled': False,
            'id': 'source_id_123',
            'description': 'Cost Center - old_cost_center_code: old_cost_center, Id - destination_id'
        }
    ]

    bulk_payload = disable_cost_centers(workspace_id, cost_centers_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_payload == payload
