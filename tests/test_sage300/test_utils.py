from apps.sage300.utils import SageDesktopConnector, Sage300Credential
from fyle_accounting_mappings.models import DestinationAttribute
from apps.mappings.models import Version
from apps.workspaces.models import Workspace
from sage_desktop_sdk.core.schema.read_only import Category


def test_sage_desktop_connector(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mock_sage_connector = mocker.patch('apps.sage300.utils.SageDesktopSDK')

    SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    assert mock_sage_connector.called


def test__create_destination_attribute(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    attribute_type = 'test'
    display_name = 'test'
    value = 'test'
    destination_id = 1
    active = True
    detail = 'test'

    expected_result = {
        'attribute_type': attribute_type,
        'display_name': display_name,
        'value': value,
        'destination_id': destination_id,
        'active': active,
        'detail': detail
    }

    assert sage_connector._create_destination_attribute(
        attribute_type=attribute_type,
        display_name=display_name,
        value=value,
        destination_id=destination_id,
        active=active,
        detail=detail
    ) == expected_result


def test__update_latest_version(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_cost_code_mappings
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    destination_attribute = DestinationAttribute.objects.filter(attribute_type='COST_CODE')
    destination_attribute.filter(value='Platform APIs').delete()
    destination_attribute.update(detail={'version': 1})

    sage_connector._update_latest_version(
        attribute_type="COST_CODE"
    )

    version = Version.objects.get(workspace_id=workspace_id)

    assert version.cost_code == 1


def test__sync_data(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    mock_data = mocker.MagicMock()
    mock_data.name = 'test'
    mock_data.id = 1
    mock_data.is_active = True
    mock_data.code = 'test'
    mock_data.version = 1

    data = [
        mock_data
    ]

    attribute_type = 'COST_CODE'
    display_name = 'test'
    destination_id = 1
    field_names = ['code', 'version']

    sage_connector._sync_data(
        data=data,
        attribute_type=attribute_type,
        display_name=display_name,
        workspace_id=workspace_id,
        field_names=field_names
    )

    assert DestinationAttribute.objects.filter(
        attribute_type=attribute_type,
        destination_id=destination_id
    ).count() == 1
    assert DestinationAttribute.objects.filter(
        attribute_type=attribute_type,
        destination_id=destination_id
    ).first().value == 'test'


def test_sync_accounts(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        account=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.name = 'test'
    mock_data.id = 1
    mock_data.is_active = True
    mock_data.code = 'test'
    mock_data.version = 1

    sage_connector.connection.accounts.get_all.return_value = [mock_data]

    result = sage_connector.sync_accounts()
    assert result == []


def test_sync_vendors(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        vendor=1,
        defaults={
            'vendor': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_vendor'
    mock_data.version = 1
    mock_data.default_expense_account = 'test_expense_account'
    mock_data.default_standard_category = 'test_category'
    mock_data.default_standard_costcode = 'test_costcode'
    mock_data.type_id = 'test_type'
    mock_data.created_on_utc = '2024-02-25'
    mock_data.name = 'test_vendor'
    mock_data.id = 1
    mock_data.is_active = True

    sage_connector.connection.vendors.get_all.return_value = [mock_data]

    result = sage_connector.sync_vendors()
    assert result == []


def test_sync_jobs(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        job=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_job'
    mock_data.status = 'test_status'
    mock_data.version = 1
    mock_data.account_prefix_id = 'test_account_prefix_id'
    mock_data.created_on_utc = '2024-02-25'
    mock_data.name = 'test_job'
    mock_data.id = 1
    mock_data.is_active = True

    sage_connector.connection.jobs.get_all_jobs.return_value = [mock_data]

    result = sage_connector.sync_jobs()
    assert result == []


def test_sync_standard_cost_codes(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        standard_cost_code=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_cost_code'
    mock_data.version = 1
    mock_data.is_standard = True
    mock_data.description = 'test_description'
    mock_data.name = 'test_cost_code'
    mock_data.id = 1
    mock_data.is_active = True

    sage_connector.connection.jobs.get_standard_costcodes.return_value = [mock_data]

    result = sage_connector.sync_standard_cost_codes()
    assert result == []


def test_sync_standard_categories(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        standard_category=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_category'
    mock_data.version = 1
    mock_data.description = 'test_description'
    mock_data.accumulation_name = 'test_accumulation_name'
    mock_data.name = 'test_category'
    mock_data.id = 1
    mock_data.is_active = True

    sage_connector.connection.jobs.get_standard_categories.return_value = [mock_data]

    result = sage_connector.sync_standard_categories()
    assert result == []


def test_sync_commitments(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        commitment=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_commitment'
    mock_data.is_closed = False
    mock_data.version = 1
    mock_data.description = 'test_description'
    mock_data.is_commited = True
    mock_data.created_on_utc = '2024-02-25'
    mock_data.date = '2024-02-25'
    mock_data.vendor_id = 'test_vendor_id'
    mock_data.job_id = 'test_job_id'
    mock_data.id = 1
    mock_data.is_active = True
    mock_data.name = 'test_commitment'

    sage_connector.connection.commitments.get_all.return_value = [mock_data]

    result = sage_connector.sync_commitments()
    assert result == []


def test_sync_commitment_items(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    DestinationAttribute.objects.create(
        attribute_type="COMMITMENT",
        display_name="test_commitment",
        value="test_commitment",
        workspace=Workspace.objects.get(id=workspace_id),
        destination_id=1,
        active=True
    )

    mock_commitment_items = mocker.MagicMock()
    mock_commitment_items.code = 'test_commitment_item'
    mock_commitment_items.version = 1
    mock_commitment_items.description = 'test_description'
    mock_commitment_items.cost_code_id = 'test_cost_code_id'
    mock_commitment_items.category_id = 'test'
    mock_commitment_items.created_on_utc = '2024-02-25'
    mock_commitment_items.job_id = 'test_job_id'
    mock_commitment_items.commitment_id = 'test_commitment_id'
    mock_commitment_items.id = 1
    mock_commitment_items.is_active = True
    mock_commitment_items.name = 'test_commitment_item'

    sage_connector.connection.commitments.get_commitment_items.return_value = [mock_commitment_items]

    sage_connector.sync_commitment_items()


def test_sync_cost_categories(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds,
    add_project_mappings
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    mock_category = mocker.Mock(spec=Category)
    mock_category.id = 1
    mock_category.job_id = '10064'
    mock_category.cost_code_id = '10064'
    mock_category.name = 'Test Category 1'
    mock_category.is_active = True

    mock_category2 = mocker.Mock(spec=Category)
    mock_category2.id = 2
    mock_category2.job_id = '10081'
    mock_category2.cost_code_id = '10064'
    mock_category2.name = 'Test Category 2'
    mock_category2.is_active = False

    categories_generator = [mock_category, mock_category2]

    sage_connector.connection.categories.get_all_categories.return_value = categories_generator

    sage_connector.sync_cost_categories()


def test_sync_cost_codes(
    db,
    mocker,
    create_temp_workspace,
    add_sage300_creds
):
    workspace_id = 1
    sage_creds = Sage300Credential.objects.get(workspace_id=workspace_id)

    mocker.patch('apps.sage300.utils.SageDesktopSDK')

    sage_connector = SageDesktopConnector(
        credentials_object=sage_creds,
        workspace_id=workspace_id
    )

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        cost_code=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = mocker.MagicMock()
    mock_data.code = 'test_cost_code'
    mock_data.version = 1
    mock_data.job_id = 'test_job_id'
    mock_data.id = 1
    mock_data.is_active = True
    mock_data.name = 'test_cost_code'

    sage_connector.connection.cost_codes.get_all_costcodes.return_value = [mock_data]

    result = sage_connector.sync_cost_codes()
    assert result == []
