from apps.mappings.imports.modules.categories import Category
from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute
from tests.test_mappings.test_imports.test_modules.fixtures import data as destination_attributes_data


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
