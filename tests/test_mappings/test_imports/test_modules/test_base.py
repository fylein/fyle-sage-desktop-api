from datetime import datetime

from fyle_accounting_mappings.models import (
    CategoryMapping,
    DestinationAttribute,
    ExpenseAttribute
)
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import Error
from apps.mappings.imports.modules.categories import Category
from apps.workspaces.models import FyleCredential
from tests.test_mappings.test_imports.test_modules.fixtures import data as destination_attributes_data
from tests.test_mappings.test_imports.test_modules.helpers import get_base_class_instance, get_platform_connection


def test_get_platform_class(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
):
    base = get_base_class_instance()
    platform = get_platform_connection(1)

    assert base.get_platform_class(platform) == platform.cost_centers

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
    )
    assert base.get_platform_class(platform) == platform.categories

    base = get_base_class_instance(
        workspace_id=1,
        source_field="COST_CENTER",
        destination_field="DEPARTMENT",
        platform_class_name="cost_centers",
    )
    assert base.get_platform_class(platform) == platform.cost_centers


def test_get_auto_sync_permission(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
):
    base = get_base_class_instance()

    assert base.get_auto_sync_permission() == False

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
    )

    assert base.get_auto_sync_permission() == True

    base = get_base_class_instance(
        workspace_id=1,
        source_field="PROJECT",
        destination_field="DEPARTMENT",
        platform_class_name="projects",
    )

    assert base.get_auto_sync_permission() == False


def test_construct_attributes_filter(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_cost_center_mappings,
):
    base = get_base_class_instance()

    assert base.construct_attributes_filter("PROJECT") == {
        "attribute_type": "PROJECT",
        "workspace_id": 1,
    }

    date_string = "2023-08-06 12:50:05.875029"
    sync_after = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
        sync_after=sync_after,
    )

    assert base.construct_attributes_filter("CATEGORY") == {
        "attribute_type": "CATEGORY",
        "workspace_id": 1,
        "updated_at__gte": sync_after,
    }

    paginated_destination_attribute_values = [
        "Mobile App Redesign",
        "Platform APIs",
        "Fyle NetSuite Integration",
        "Fyle Sage Intacct Integration",
        "Support Taxes",
        "T&M Project with Five Tasks",
        "Fixed Fee Project with Five Tasks",
        "General Overhead",
        "General Overhead-Current",
        "Youtube proj",
        "Integrations",
        "Yujiro",
        "Pickle",
    ]

    assert base.construct_attributes_filter(
        "COST_CENTER", paginated_destination_attribute_values
    ) == {
        "attribute_type": "COST_CENTER",
        "workspace_id": 1,
        "updated_at__gte": sync_after,
        "value__in": paginated_destination_attribute_values,
    }


def test_remove_duplicates(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_cost_center_mappings,
):
    attributes = DestinationAttribute.objects.filter(attribute_type="COST_CENTER")

    assert len(attributes) == 6

    for attribute in attributes:
        DestinationAttribute.objects.create(
            attribute_type="COST_CENTER",
            workspace_id=attribute.workspace_id,
            value=attribute.value,
            destination_id="010{0}".format(attribute.destination_id),
        )

    attributes = DestinationAttribute.objects.filter(attribute_type="COST_CENTER")

    assert len(attributes) == 12

    base = get_base_class_instance()

    attributes = base.remove_duplicate_attributes(attributes)
    assert len(attributes) == 2


def test_resolve_expense_attribute_errors(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_expense_destination_attributes,
):
    workspace_id = 1
    category = Category(1, "ACCOUNT", None)

    # deleting all the Error objects
    Error.objects.filter(workspace_id=workspace_id).delete()

    # getting the expense_attribute
    source_category = ExpenseAttribute.objects.filter(
        workspace_id=1, attribute_type="CATEGORY"
    ).first()

    category_mapping_count = CategoryMapping.objects.filter(
        workspace_id=1, source_category_id=source_category.id
    ).count()

    # category mapping is not present
    assert category_mapping_count == 0

    error = Error.objects.create(
        workspace_id=workspace_id,
        expense_attribute=source_category,
        type="CATEGORY_MAPPING",
        error_title=source_category.value,
        error_detail="Category mapping is missing",
        is_resolved=False,
    )

    assert Error.objects.get(id=error.id).is_resolved == False

    destination_attribute = DestinationAttribute.objects.filter(
        workspace_id=1, attribute_type="ACCOUNT"
    ).first()

    # creating the category mapping in bulk mode to avoid setting the is_resolved flag to true by signal
    category_list = []
    category_list.append(
        CategoryMapping(
            workspace_id=1,
            source_category_id=source_category.id,
            destination_account_id=destination_attribute.id,
        )
    )
    CategoryMapping.objects.bulk_create(category_list)

    category.resolve_expense_attribute_errors()
    assert Error.objects.get(id=error.id).is_resolved == True


def test_sync_expense_atrributes(
    mocker,
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds
):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.org_id = "orwimNcVyYsp"
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch("fyle.platform.apis.v1beta.admin.Categories.list_all", return_value=[])

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    category = Category(workspace_id, "ACCOUNT", None)
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    mocker.patch(
        "fyle.platform.apis.v1beta.admin.Categories.list_all",
        return_value=destination_attributes_data[
            "create_new_auto_create_categories_expense_attributes_0"
        ],
    )
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert (
        category_count
        == destination_attributes_data[
            "create_new_auto_create_categories_expense_attributes_0"
        ][0]["count"]
    )


def test_sync_destination_attributes(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    mocker
):
    def test():
        pass

    mock_connection = mocker.patch(
        "apps.mappings.imports.modules.base.SageDesktopConnector"
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_standard_categories",
        return_value=test
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_standard_cost_codes",
        return_value=test
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_jobs",
        return_value=test
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_vendors",
        return_value=test
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_accounts",
        return_value=test
    )

    mocker.patch.object(
        mock_connection.return_value,
        "sync_commitments",
        return_value=test
    )

    base = get_base_class_instance()

    base.sync_destination_attributes("STANDARD_CATEGORY")
    mock_connection.return_value.sync_standard_categories.assert_called_once()

    base.sync_destination_attributes("STANDARD_COST_CODE")
    mock_connection.return_value.sync_standard_cost_codes.assert_called_once()

    base.sync_destination_attributes("JOB")
    mock_connection.return_value.sync_jobs.assert_called_once()

    base.sync_destination_attributes("VENDOR")
    mock_connection.return_value.sync_vendors.assert_called_once()

    base.sync_destination_attributes("ACCOUNT")
    mock_connection.return_value.sync_accounts.assert_called_once()

    base.sync_destination_attributes("COMMITMENT")
    mock_connection.return_value.sync_commitments.assert_called_once()
