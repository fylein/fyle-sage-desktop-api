from apps.mappings.imports.modules.projects import Project
from apps.workspaces.models import ImportSetting
from fyle_accounting_mappings.models import DestinationAttribute
from .fixtures import data


def test_construct_fyle_payload(api_client, test_connection, mocker, create_temp_workspace, add_cost_category, add_sage300_creds, add_fyle_credentials, add_project_mappings):
    project = Project(1, 'PROJECT', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')

    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = project.get_auto_sync_permission()

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == data['create_fyle_project_payload_create_new_case']

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1,
        attribute_type='PROJECT',
        value__in=['Platform APIs']
    ).update(active=False)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')

    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes]

    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == data['create_fyle_project_payload_create_disable_case']

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')
    paginated_destination_attributes.update(active=False)

    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes]

    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)
    existing_fyle_attributes_map['platform apis'] = '10081'
    existing_fyle_attributes_map['direct mail campaign'] = '10064'

    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == data['create_fyle_project_payload_create_disable_case2']


def test_get_existing_fyle_attributes(db, create_temp_workspace, add_project_mappings, add_import_settings):
    project = Project(1, 'PROJECT', None)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='JOB')
    paginated_destination_attributes_without_duplicates = project.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {}

    # with code prepending
    project.use_code_in_naming = True
    paginated_destination_attributes_without_duplicates = project.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123 cre platform': '10065', '123 integrations cre': '10082'}


def test_construct_fyle_payload_with_code(db, create_temp_workspace, add_project_mappings, add_cost_category, add_import_settings):
    project = Project(1, 'PROJECT', None, True)
    project.use_code_in_naming = True

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='JOB')
    paginated_destination_attributes_without_duplicates = project.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = project.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = project.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == data["create_fyle_project_payload_with_code_create_new_case"]
