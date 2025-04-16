import pytest
from unittest.mock import MagicMock
from apps.sage300.utils import SageDesktopConnector, Sage300Credential
from fyle_accounting_mappings.models import DestinationAttribute
from apps.mappings.models import Version
from apps.workspaces.models import Workspace
from fyle_integrations_imports.models import ImportLog
from sage_desktop_sdk.core.schema.read_only import CommitmentItem


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
    code = '123'

    expected_result = {
        'attribute_type': attribute_type,
        'display_name': display_name,
        'value': value,
        'destination_id': destination_id,
        'active': active,
        'detail': detail,
        'code': code
    }

    assert sage_connector._create_destination_attribute(
        attribute_type=attribute_type,
        display_name=display_name,
        value=value,
        destination_id=destination_id,
        active=active,
        detail=detail,
        code=code
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
        data_gen=data,
        attribute_type=attribute_type,
        display_name=display_name,
        workspace_id=workspace_id,
        field_names=field_names,
        is_generator=False
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

    mock_data = {
        'Code': 'test',
        'Version': 1,
        'Name': 'test',
        'Id': 1,
        'IsActive': True
    }

    sage_connector.connection.accounts.get_all.return_value = [[[mock_data]]]

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

    mock_data = {
        'Code': 'test',
        'Version': 1,
        'Name': 'test',
        'Id': 1,
        'IsActive': True,
        'DefaultExpenseAccount': 'test',
        'DefaultStandardCategory': 'test',
        'DefaultStandardCostCode': 'test',
        'TypeId': 'test',
        'CreatedOnUtc': '2024-02-25'
    }

    sage_connector.connection.vendors.get_all.return_value = [[[mock_data]]]

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

    mock_data = {
        'Code': 'test_job',
        'Status': 'test_status',
        'Version': 1,
        'AccountPrefixId': 'test_account_prefix_id',
        'CreatedOnUtc': '2024-02-25',
        'Id': 1,
        'IsActive': True,
        'Name': 'test_job'
    }

    sage_connector.connection.jobs.get_all_jobs.return_value = [[[mock_data]]]

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

    mock_data = {
        'Code': 'test_cost_code',
        'Version': 1,
        'IsStandard': True,
        'Description': 'test_description',
        'Name': 'test_cost_code',
        'Id': 1,
        'IsActive': True
    }

    sage_connector.connection.jobs.get_standard_costcodes.return_value = [[[mock_data]]]

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

    mock_data = {
        'Code': 'test_category',
        'Version': 1,
        'Description': 'test_description',
        'AccumulationName': 'test_accumulation_name',
        'Name': 'test_category',
        'Id': 1,
        'IsActive': True
    }

    sage_connector.connection.jobs.get_standard_categories.return_value = [[[mock_data]]]

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

    mock_data = {
        'Code': 'test_commitment',
        'IsClosed': False,
        'Version': 1,
        'Description': 'test_description',
        'IsCommited': True,
        'CreatedOnUtc': '2024-02-25',
        'Date': '2024-02-25',
        'VendorId': 'test_vendor_id',
        'JobId': 'test_job_id',
        'Id': 1,
        'IsActive': True,
        'Name': 'test_commitment'
    }

    sage_connector.connection.commitments.get_all.return_value = [[[mock_data]]]

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

    cost_category_import_log = ImportLog.update_or_create_in_progress_import_log('COST_CATEGORY', workspace_id)

    mock_category = [{
        "Id": 1,
        "JobId": "10064",
        "CostCodeId": "10064",
        "Name": "Test Category 1",
        "IsActive": True,
        "Version": 1,
    },{
        "Id": 2,
        "JobId": "10081",
        "CostCodeId": "10064",
        "Name": "Test Category 2",
        "IsActive": False,
        "Version": '2'
    }]

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'cost_category': 1
        }
    )

    categories_generator = [[mock_category]]

    sage_connector.connection.categories.get_all_categories.return_value = categories_generator

    sage_connector.sync_cost_categories(cost_category_import_log)

    assert Version.objects.get(workspace_id=workspace_id).cost_category == 2


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

    cost_code_import_log = ImportLog.update_or_create_in_progress_import_log('COST_CODE', workspace_id)

    Version.objects.update_or_create(
        workspace_id=workspace_id,
        cost_code=1,
        defaults={
            'cost_code': 1
        }
    )

    mock_data = {
        'Code': 'test_cost_code',
        'Version': 1,
        'JobId': 'test_job_id',
        'Id': 1,
        'IsActive': True,
        'Name': 'test_cost_code'
    }

    sage_connector.connection.cost_codes.get_all_costcodes.return_value = [[[mock_data]]]

    result = sage_connector.sync_cost_codes(cost_code_import_log)
    assert result == []


def test_bulk_create_or_update_destination_attributes_with_code(db, create_temp_workspace):
    workspace_id = 1

    # Dummy data for testing
    attributes = [
        {
            'attribute_type': 'COST_CODE',
            'display_name': 'Display 1',
            'value': 'Value 1',
            'destination_id': 'DestID1',
            'detail': {'info': 'Detail 1'},
            'active': True,
            'code': 'Code1'
        },
        {
            'attribute_type': 'COST_CODE',
            'display_name': 'Display 2',
            'value': 'Value 2',
            'destination_id': 'DestID2',
            'detail': {'info': 'Detail 2'},
            'active': False,
            'code': 'Code2'
        }
    ]

    # Call the function to test
    DestinationAttribute.bulk_create_or_update_destination_attributes(
        attributes=attributes,
        attribute_type='COST_CODE',
        workspace_id=workspace_id,
        update=True
    )

    # Verify creation
    assert DestinationAttribute.objects.filter(destination_id='DestID1').exists()
    assert DestinationAttribute.objects.filter(destination_id='DestID2').exists()

    # Update data
    attributes[0]['value'] = 'Updated Value 1'
    attributes[1]['value'] = 'Updated Value 2'
    attributes[0]['code'] = 'Updated Code1'
    attributes[1]['code'] = 'Updated Code2'
    DestinationAttribute.bulk_create_or_update_destination_attributes(
        attributes=attributes,
        attribute_type='COST_CODE',
        workspace_id=workspace_id,
        update=True
    )

    # Verify update
    destination_attributes = DestinationAttribute.objects.filter(destination_id__in=['DestID1', 'DestID2'])
    destination_attributes_dict = {attr.destination_id: attr for attr in destination_attributes}

    assert destination_attributes_dict['DestID1'].value == 'Updated Value 1'
    assert destination_attributes_dict['DestID2'].value == 'Updated Value 2'
    assert destination_attributes_dict['DestID1'].code == 'Updated Code1'
    assert destination_attributes_dict['DestID2'].code == 'Updated Code2'


def test_bulk_create_or_update_destination_attributes_without_code(db, create_temp_workspace):
    workspace_id = 1

    # Dummy data for testing
    attributes = [
        {
            'attribute_type': 'COST_CODE',
            'display_name': 'Display 1',
            'value': 'Value 1',
            'destination_id': 'DestID1',
            'detail': {'info': 'Detail 1'},
            'active': True,
        },
        {
            'attribute_type': 'COST_CODE',
            'display_name': 'Display 2',
            'value': 'Value 2',
            'destination_id': 'DestID2',
            'detail': {'info': 'Detail 2'},
            'active': False,
        }
    ]

    # Call the function to test
    DestinationAttribute.bulk_create_or_update_destination_attributes(
        attributes=attributes,
        attribute_type='COST_CODE',
        workspace_id=workspace_id,
        update=True
    )

    # Verify creation
    assert DestinationAttribute.objects.filter(destination_id='DestID1').exists()
    assert DestinationAttribute.objects.filter(destination_id='DestID2').exists()

    # Update data
    attributes[0]['value'] = 'Updated Value 1'
    attributes[1]['value'] = 'Updated Value 2'
    DestinationAttribute.bulk_create_or_update_destination_attributes(
        attributes=attributes,
        attribute_type='COST_CODE',
        workspace_id=workspace_id,
        update=True
    )

    # Verify update
    assert DestinationAttribute.objects.get(destination_id='DestID1').value == 'Updated Value 1'
    assert DestinationAttribute.objects.get(destination_id='DestID2').value == 'Updated Value 2'


@pytest.fixture
def sync_instance(
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

    return sage_connector


def test_sync_data_with_generator(sync_instance, mocker):
    # Mock dependencies
    mock_mapping_setting = mocker.patch('apps.sage300.utils.MappingSetting')
    mock_bulk_create = mocker.patch('apps.sage300.utils.DestinationAttribute.bulk_create_or_update_destination_attributes')
    mock_get_attribute_class = mocker.patch('apps.sage300.utils.SageDesktopConnector._get_attribute_class')
    mock_update_latest_version = mocker.patch('apps.sage300.utils.SageDesktopConnector._update_latest_version')
    mock_import_string = mocker.patch('apps.sage300.utils.import_string')

    # Setup mock return values
    mock_mapping_setting.objects.filter.return_value.first.return_value = MagicMock(is_custom=False, source_field='PROJECT', destination_field='JOB')
    mock_get_attribute_class.return_value = 'Job'
    mock_update_latest_version.return_value = None
    mock_import_string.return_value.from_dict.return_value = MagicMock()

    # Mock data generator
    data_gen = iter([iter([{'key': 'value'}])])

    # Call method
    sync_instance._sync_data(data_gen, 'JOB', 'job', 1, ['code', 'version'], is_generator=True)

    # Assertions
    mock_bulk_create.assert_called_once()
    called_args = mock_bulk_create.call_args[0]

    assert called_args[1] == 'JOB'
    assert called_args[2] == 1
    assert mock_bulk_create.call_args[1]['attribute_disable_callback_path'] == 'fyle_integrations_imports.modules.projects.disable_projects'  # ATTRIBUTE_CALLBACK_MAP['PROJECT']


def test_sync_data_without_generator(sync_instance, mocker):
    # Mock dependencies
    mock_bulk_create = mocker.patch('apps.sage300.utils.DestinationAttribute.bulk_create_or_update_destination_attributes')
    mock_get_attribute_class = mocker.patch('apps.sage300.utils.SageDesktopConnector._get_attribute_class')
    mock_update_latest_version = mocker.patch('apps.sage300.utils.SageDesktopConnector._update_latest_version')
    mock_import_string = mocker.patch('apps.sage300.utils.import_string')

    # Setup mock return values
    mock_get_attribute_class.return_value = 'CommitmentItem'
    mock_update_latest_version.return_value = None
    mock_import_string.return_value.from_dict.return_value = MagicMock()

    # Mock data
    data = [
        CommitmentItem(
            id='ffb326e3-783f-4667-a443-b06c0083ef07',
            version=212585,
            amount=250.0,
            amount_approved=0.0,
            amount_invoiced=591.0,
            amount_paid=0.0,
            amount_original=250.0,
            amount_pending=0.0,
            amount_retained=22.5,
            category_id='ece00064-b585-4f87-b0bc-b06100a9bec8',
            code='1',
            commitment_id='ddb74931-f138-4e2e-a1f6-b06c0083edd5',
            cost_code_id='d3b321be-1e6c-4d4b-add4-b06100a9bd2c',
            created_on_utc='2023-08-28T08:00:21Z',
            description='',
            has_external_id=True,
            is_active=True,
            is_archived=False,
            job_id='5e0eb476-b189-4409-b9b3-b061009602a4',
            name='Refrigeration',
            standard_category_id='302918fb-2f89-4d7f-972a-b05b00f3c431',
            tax=0.0,
            tax_group_id='a721a071-9cac-4134-9d8b-b05b00f3cb2a',
            tax_group_code='EXMPT',
            unit_cost=0.0,
            units=0.0
        )
    ]

    # Call method
    sync_instance._sync_data(data, 'COMMITMENT_ITEM', 'commitment_item', 1, ['code', 'version'], is_generator=False)

    # Assertions
    mock_bulk_create.assert_called_once()
    called_args = mock_bulk_create.call_args[0]
    assert called_args[1] == 'COMMITMENT_ITEM'
    assert called_args[2] == 1
    assert len(called_args) == 4
