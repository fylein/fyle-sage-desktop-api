from apps.workspaces.models import ImportSetting
from apps.mappings.imports.modules.categories import Category, disable_categories
from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute
from tests.test_mappings.test_imports.test_modules.fixtures import data as destination_attributes_data
from .fixtures import data


def test_construct_fyle_payload(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_expense_destination_attributes_1,
    mocker,
):
    category = Category(1, "ACCOUNT", None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    )
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = category.get_auto_sync_permission()

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert (
        fyle_payload
        == destination_attributes_data["create_fyle_category_payload_create_new_case"]
    )

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT", value__in=["Internet", "Meals"]
    ).update(active=False)

    ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT", value__in=["Internet", "Meals"]
    ).update(active=True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    )

    paginated_destination_attribute_values = [
        attribute.value for attribute in paginated_destination_attributes
    ]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(
        paginated_destination_attribute_values
    )

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed,
    )

    assert (
        fyle_payload
        == destination_attributes_data[
            "create_fyle_category_payload_create_disable_case"
        ]
    )


def test_create_mappings(
    db,
    create_temp_workspace,
    add_expense_destination_attributes_1
):
    workspace_id = 1

    category = Category(workspace_id, "ACCOUNT", None)

    category.create_mappings()

    category_mappings = CategoryMapping.objects.filter(workspace_id=workspace_id)

    assert category_mappings.count() == 2
    assert category_mappings[0].destination_account.value == "Internet"
    assert category_mappings[1].destination_account.value == "Meals"


def test_get_existing_fyle_attributes(
    db,
    create_temp_workspace,
    add_expense_destination_attributes_1,
    add_expense_destination_attributes_3,
    add_import_settings
):
    category = Category(1, 'ACCOUNT', None)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT')
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'internet': '10091', 'meals': '10092'}

    # with code prepending
    category.use_code_in_naming = True
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT', code__isnull=False)
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123: sage300': '10095'}


def test_construct_fyle_payload_with_code(
    db,
    create_temp_workspace,
    add_expense_destination_attributes_1,
    add_expense_destination_attributes_3,
    add_import_settings
):
    category = Category(1, 'ACCOUNT', None, True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='ACCOUNT')
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == data["create_fyle_category_payload_with_code_create_new_case"]


def test_disable_categories(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials,
    add_expense_destination_attributes_1,
    add_import_settings
):
    workspace_id = 1

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'old_category_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='old_category',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('apps.mappings.imports.modules.categories.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.categories, 'post_bulk')

    disable_categories(workspace_id, categories_to_disable, is_import_to_fyle_enabled=True)

    assert bulk_post_call.call_count == 1

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category_2',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'new_category_code'
        }
    }

    disable_categories(workspace_id, categories_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = ImportSetting.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['ACCOUNT']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='old_category_code: old_category',
        source_id='source_id_123',
        active=True
    )

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'old_category_code'
        }
    }

    payload = [{
        'name': 'old_category_code: old_category',
        'code': 'destination_id',
        'is_enabled': False,
        'id': 'source_id_123'
    }]

    bulk_payload = disable_categories(workspace_id, categories_to_disable, is_import_to_fyle_enabled=True)
    assert bulk_payload == payload
