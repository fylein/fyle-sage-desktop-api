from datetime import datetime

from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute, ExpenseAttribute, Mapping
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import Error
from apps.sage300.utils import SageDesktopConnector
from apps.workspaces.models import FyleCredential
from fyle_integrations_imports.models import ImportLog
from fyle_integrations_imports.modules.categories import Category
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


def test_construct_attributes_filter(
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_cost_center_mappings,
):
    base = get_base_class_instance()
    assert base.construct_attributes_filter("PROJECT") == {'attribute_type': 'PROJECT', 'workspace_id': 1, 'active': True}

    date_string = "2023-08-06 12:50:05.875029"
    sync_after = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")

    base = get_base_class_instance(
        workspace_id=1,
        source_field="CATEGORY",
        destination_field="ACCOUNT",
        platform_class_name="categories",
        sync_after=sync_after,
    )

    assert base.construct_attributes_filter("CATEGORY") == {'attribute_type': 'CATEGORY', 'workspace_id': 1, 'active': True, 'updated_at__gte': sync_after}

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
    ) == {'attribute_type': 'COST_CENTER', 'workspace_id': 1, 'active': True, 'updated_at__gte': sync_after}


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
    mocker,
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_sage300_creds,
    add_expense_destination_attributes,
):
    workspace_id = 1
    category = Category(1, "ACCOUNT", None, sdk_connection=mocker.Mock(), destination_sync_methods=['accounts'], is_auto_sync_enabled=True, is_3d_mapping=False, use_mapping_table=False, charts_of_accounts=None)

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

    mocker.patch("fyle.platform.apis.v1.admin.Categories.list_all", return_value=[])

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    category = Category(workspace_id, "ACCOUNT", None, sdk_connection=mocker.Mock(), destination_sync_methods=['accounts'], is_auto_sync_enabled=True, is_3d_mapping=False, charts_of_accounts=None)
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type="CATEGORY"
    ).count()
    assert category_count == 0

    mocker.patch(
        "fyle.platform.apis.v1.admin.Categories.list_all",
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

    mocker.patch(
        "apps.sage300.utils.SageDesktopConnector.__init__",
        return_value=None
    )

    mock_connection = mocker.patch(
        "apps.sage300.utils.SageDesktopConnector",
        return_value=mocker.Mock(spec=SageDesktopConnector)
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

    base = get_base_class_instance(destination_sync_methods = ["jobs"], sdk_connection = mock_connection.return_value)

    base.sync_destination_attributes()
    mock_connection.return_value.sync_jobs.assert_called_once()

    base = get_base_class_instance(destination_sync_methods = ["vendors"], sdk_connection = mock_connection.return_value)
    base.sync_destination_attributes()
    mock_connection.return_value.sync_vendors.assert_called_once()

    base = get_base_class_instance(destination_sync_methods = ["accounts"], sdk_connection = mock_connection.return_value)
    base.sync_destination_attributes()
    mock_connection.return_value.sync_accounts.assert_called_once()


def test_import_destination_attribute_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_fyle_credentials
):
    base = get_base_class_instance()

    mocker.patch('fyle_integrations_imports.modules.base.PlatformConnector')

    mocker.patch.object(
        base,
        'sync_destination_attributes',
    )
    mocker.patch.object(
        base,
        'construct_payload_and_import_to_fyle',
    )
    mocker.patch.object(
        base,
        'sync_expense_attributes',
    )
    mocker.patch.object(
        base,
        'create_mappings',
    )

    mocker.patch.object(
        base,
        'resolve_expense_attribute_errors',
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    base.import_destination_attribute_to_fyle(import_log)
    assert True


def test_create_mappings(
    db,
    mocker,
    create_temp_workspace,
    add_cost_center_mappings
):
    workspace_id = 1
    base = get_base_class_instance()

    values = DestinationAttribute.objects.filter(workspace_id=workspace_id, value__in=["Direct Mail Campaign", "Platform APIs"])

    base.create_mappings(values)

    mappings = Mapping.objects.filter(workspace_id=workspace_id)

    assert mappings.count() == 2
    assert mappings[0].destination.value == "Direct Mail Campaign"
    assert mappings[1].destination.value == "Platform APIs"


def test_construct_payload_and_import_to_fyle(
    db,
    mocker,
    create_temp_workspace,
    add_cost_center_mappings
):
    base = get_base_class_instance()

    platform = mocker.patch('fyle_integrations_imports.modules.base.PlatformConnector')
    mocker.patch.object(
        base,
        'post_to_fyle_and_sync',
    )
    mocker.patch.object(
        base,
        'setup_fyle_payload_creation',
        return_value = {
            'attribute_type': 'COST_CENTER',
            'workspace_id': 1,
            'attribute_values': [
                {
                    'display_name': 'Direct Mail Campaign',
                    'value': 'Direct Mail Campaign',
                    'source_id': '10064',
                    'detail': 'Cost Center - Direct Mail Campaign, Id - 10064',
                    'active': True
                },
                {
                    'display_name': 'Platform APIs',
                    'value': 'Platform APIs',
                    'source_id': '10081',
                    'detail': 'Cost Center - Platform APIs, Id - 10081',
                    'active': True
                }
            ]
        }
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    base.construct_payload_and_import_to_fyle(platform, import_log)

    import_log.refresh_from_db()
    assert import_log.total_batches_count == 1

    destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='COST_CENTER')
    destination_attributes.delete()

    base.construct_payload_and_import_to_fyle(platform, import_log)

    import_log.refresh_from_db()

    assert import_log.total_batches_count == 0
    assert import_log.status == 'COMPLETE'


def test_post_to_fyle_and_sync(
    db,
    mocker,
    create_temp_workspace
):
    base = get_base_class_instance()

    platform = mocker.patch('fyle_integrations_imports.modules.base.PlatformConnector')
    mocker.patch.object(
        platform.return_value,
        'post'
    )
    mocker.patch.object(
        platform.return_value,
        'bulk_post'
    )

    import_log = ImportLog(
        workspace_id=1,
        attribute_type='CUSTOM',
        status='IN_PROGRESS',
        error_log={},
        last_successful_run_at="2024-01-01T00:00:00Z",
    )

    assert base.platform_class_name == 'cost_centers'

    base.post_to_fyle_and_sync(
        fyle_payload=[{
            'field_name': 'Custom',
            'type': 'SELECT',
            'is_enabled': True
        }],
        resource_class=platform.return_value,
        is_last_batch=True,
        import_log=import_log
    )

    import_log.refresh_from_db()
    import_log.status = 'COMPLETE'


def test_check_import_log_and_start_import(
    db,
    mocker,
    create_temp_workspace
):
    base = get_base_class_instance()

    mocker.patch.object(
        base,
        'import_destination_attribute_to_fyle',
    )

    base.check_import_log_and_start_import()

    import_log = ImportLog.objects.get(workspace_id=1, attribute_type='COST_CENTER')

    assert import_log.status == 'IN_PROGRESS'

    base.check_import_log_and_start_import()

    import_log.refresh_from_db()
    assert import_log.status == 'IN_PROGRESS'
