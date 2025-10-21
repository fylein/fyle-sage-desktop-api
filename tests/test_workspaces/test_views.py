import json

import pytest  # noqa
from django.urls import reverse
from django_q.models import Schedule
from fyle_accounting_mappings.models import MappingSetting

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import AdvancedSetting, ExportSetting, FeatureConfig, Sage300Credential, Workspace
from fyle_integrations_imports.models import ImportLog
from sage_desktop_sdk.exceptions.hh2_exceptions import InvalidUserCredentials
from tests.helper import dict_compare_keys
from tests.test_fyle.fixtures import fixtures as data


def test_post_of_workspace(api_client, test_connection):
    '''
    Test post of workspace
    '''
    Workspace.objects.all().delete()
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace = Workspace.objects.filter(org_id='orNoatdUnm1w').first()

    assert response.status_code == 201
    assert workspace.name == response.data['name']
    assert workspace.org_id == response.data['org_id']

    response = json.loads(response.content)

    response = api_client.post(url)
    assert response.status_code == 201


def test_get_of_workspace(api_client, test_connection):
    '''
    Test get of workspace
    '''
    Workspace.objects.all().delete()
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 400
    assert response.data['message'] == 'org_id is missing'

    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 400
    assert response.data['message'] == 'Workspace not found or the user does not have access to workspaces'

    response = api_client.post(url)
    response = api_client.get('{}?org_id=orNoatdUnm1w'.format(url))

    assert response.status_code == 200
    assert response.data['name'] == 'Fyle For MS Dynamics Demo'
    assert response.data['org_id'] == 'orNoatdUnm1w'


def test_post_of_sage300_creds(api_client, test_connection, mocker):
    '''
    Test post of sage300 creds with identifier normalization
    '''
    Workspace.objects.all().delete()
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse('sage300-creds', kwargs={'workspace_id': response.data['id']})

    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        return_value={'text': {'Result': 2}}
    )

    base_payload = {
        'password': "password",
        'username': "username",
        'workspace': response.data['id']
    }

    test_cases = [
        "https://centurymechanicalcontractorsinc.hh2.com",
        "http://centurymechanicalcontractorsinc.hh2.com",
        "centurymechanicalcontractorsinc",
        "centurymechanicalcontractorsinc.hh2.com"
    ]

    for test_case in test_cases:
        payload = base_payload.copy()
        payload['identifier'] = test_case

        response = api_client.post(url, payload)
        assert response.status_code == 201, f"Failed for test case: {test_case}"

        sage300_cred = Sage300Credential.objects.get(workspace_id=response.data['workspace'])
        assert sage300_cred.identifier == 'centurymechanicalcontractorsinc.hh2.com', f"Identifier normalization failed for test case: {test_case}"

        sage300_cred.delete()


def test_get_of_sage300_creds(api_client, test_connection):
    '''
    Test get of workspace
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse('sage300-creds', kwargs={'workspace_id': response.data['id']})

    Sage300Credential.objects.create(
        identifier='identifier',
        username='username',
        password='password',
        workspace_id=response.data['id'],
        api_key='apiley',
        api_secret='apisecret'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['username'] == 'username'
    assert response.data['password'] == 'password'


def test_update_sage300_creds(api_client, test_connection, mocker):
    '''
    Test update of sage300 creds with identifier normalization and error handling
    '''
    # Create workspace first
    Workspace.objects.all().delete()
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)
    workspace_id = response.data['id']

    # Create initial credentials
    Sage300Credential.objects.create(
        identifier='old-identifier.hh2.com',
        username='old_username',
        password='old_password',
        workspace_id=workspace_id,
        api_key='old_api_key',
        api_secret='old_api_secret',
        is_expired=True
    )

    url = reverse('sage300-creds', kwargs={'workspace_id': workspace_id})

    # Mock successful sage300 connection
    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        return_value={'text': {'Result': 2}}
    )
    mocker.patch(
        'apps.workspaces.tasks.patch_integration_settings',
        return_value=None
    )

    # Test cases for identifier normalization during update
    test_cases = [
        {
            'input': "https://newcompany.hh2.com",
            'expected': 'newcompany.hh2.com',
            'description': 'https:// prefix removal'
        },
        {
            'input': "http://anothercompany.hh2.com",
            'expected': 'anothercompany.hh2.com',
            'description': 'http:// prefix removal'
        },
        {
            'input': "thirdcompany",
            'expected': 'thirdcompany.hh2.com',
            'description': '.hh2.com suffix addition'
        },
        {
            'input': "fourthcompany.hh2.com",
            'expected': 'fourthcompany.hh2.com',
            'description': 'no change needed'
        }
    ]

    for test_case in test_cases:
        # Update payload
        payload = {
            'username': 'updated_username',
            'password': 'updated_password',
            'identifier': test_case['input'],
            'workspace': workspace_id
        }

        response = api_client.put(url, payload)
        assert response.status_code == 200, f"Failed for test case: {test_case['description']}"

        # Verify the credentials were updated
        updated_cred = Sage300Credential.objects.get(workspace_id=workspace_id)
        assert updated_cred.username == 'updated_username', f"Username not updated for: {test_case['description']}"
        assert updated_cred.password == 'updated_password', f"Password not updated for: {test_case['description']}"
        assert updated_cred.identifier == test_case['expected'], f"Identifier normalization failed for: {test_case['description']}"
        assert updated_cred.is_expired == False, f"is_expired not reset for: {test_case['description']}"

    # Test partial update (only updating username)
    payload = {
        'username': 'partially_updated_username',
        'password': 'updated_password',  # Keep existing password
        'identifier': 'fourthcompany.hh2.com',  # Keep existing identifier
        'workspace': workspace_id
    }
    response = api_client.put(url, payload)
    assert response.status_code == 200

    updated_cred = Sage300Credential.objects.get(workspace_id=workspace_id)
    assert updated_cred.username == 'partially_updated_username'
    assert updated_cred.password == 'updated_password'  # Should remain unchanged
    assert updated_cred.identifier == 'fourthcompany.hh2.com'  # Should remain unchanged from last test

    # Test update with connection failure
    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        side_effect=Exception('Connection failed')
    )

    payload = {
        'username': 'failed_username',
        'password': 'failed_password',
        'identifier': 'failedcompany.hh2.com',
        'workspace': workspace_id
    }

    response = api_client.put(url, payload)
    assert response.status_code == 400
    assert 'Invalid Login Attempt' in str(response.data)

    # Verify credentials were not updated after failure
    unchanged_cred = Sage300Credential.objects.get(workspace_id=workspace_id)
    assert unchanged_cred.username == 'partially_updated_username'  # Should remain unchanged
    assert unchanged_cred.password == 'updated_password'  # Should remain unchanged


def test_export_settings(api_client, test_connection):
    '''
    Test export settings
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('export-settings', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)
    assert response.status_code == 400

    payload = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'reimbursable_expense_state': 'PAYMENT_PROCESSING',
        'reimbursable_expense_date': 'LAST_SPENT_AT',
        'reimbursable_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_export_type': 'DIRECT_COST',
        'credit_card_expense_state': 'PAID',
        'credit_card_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_date': 'POSTED_AT',
        'default_reimbursable_account_name': 'reimbursable account',
        'default_reimbursable_account_id': '123',
        'default_ccc_credit_card_account_name': 'CCC credit card account',
        'default_ccc_credit_card_account_id': '123',
        'default_reimbursable_credit_card_account_name': 'reimbursable credit card account',
        'default_reimbursable_credit_card_account_id': '342',
        'default_vendor_name': 'Nilesh',
        'default_vendor_id': '123',
        'default_back_account_id': '123',
        'default_bank_account_name': 'Bank account'
    }

    response = api_client.post(url, payload)

    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    assert response.status_code == 201
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'LAST_SPENT_AT'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'DIRECT_COST'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'POSTED_AT'
    assert export_settings.default_reimbursable_account_name == 'reimbursable account'
    assert export_settings.default_reimbursable_account_id == '123'
    assert export_settings.default_ccc_credit_card_account_name == 'CCC credit card account'
    assert export_settings.default_ccc_credit_card_account_id == '123'
    assert export_settings.default_reimbursable_credit_card_account_name == 'reimbursable credit card account'
    assert export_settings.default_reimbursable_credit_card_account_id == '342'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'

    response = api_client.get(url)

    assert response.status_code == 200
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'LAST_SPENT_AT'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'DIRECT_COST'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'POSTED_AT'
    assert export_settings.default_reimbursable_account_name == 'reimbursable account'
    assert export_settings.default_reimbursable_account_id == '123'
    assert export_settings.default_ccc_credit_card_account_name == 'CCC credit card account'
    assert export_settings.default_ccc_credit_card_account_id == '123'
    assert export_settings.default_reimbursable_credit_card_account_name == 'reimbursable credit card account'
    assert export_settings.default_reimbursable_credit_card_account_id == '342'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'


def test_import_settings(mocker, api_client, test_connection, create_temp_workspace, add_sage300_creds, add_fyle_credentials):
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.get_by_id',
        return_value={
            'options': ['samp'],
            'updated_at': '2020-06-11T13:14:55.201598+00:00',
            'is_mandatory': False
        }
    )
    mocker.patch(
        'apps.sage300.utils.SageDesktopConnector.__init__',
        return_value=None
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.post',
        return_value = {
            "data": {"id": 12}
        }
    )
    mocker.patch(
        'fyle_integrations_platform_connector.apis.ExpenseCustomFields.sync',
        return_value=None
    )

    mocker.patch(
        'fyle_integrations_platform_connector.apis.DependentFields.get_project_field_id',
        return_value=12
    )

    workspace = Workspace.objects.get(id=1)
    workspace.onboarding_state = 'IMPORT_SETTINGS'
    workspace.save()

    url = reverse('import-settings', kwargs={'workspace_id': 1})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings_payload'],
        format='json'
    )

    assert response.status_code == 200

    response = json.loads(response.content)
    assert dict_compare_keys(response, data['response']) == [], 'workspaces api returns a diff in the keys'

    response = api_client.put(
        url,
        data=data['import_settings_without_mapping'],
        format='json'
    )
    assert response.status_code == 200

    # Test if import_projects add schedule or not
    url = reverse('import-settings', kwargs={'workspace_id': 1})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.put(
        url,
        data=data['import_settings_schedule_check'],
        format='json'
    )

    assert response.status_code == 200

    mapping = MappingSetting.objects.filter(workspace_id=1, source_field='PROJECT').first()

    assert mapping.import_to_fyle == True

    schedule = Schedule.objects.filter(
        func='apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle',
        args='{}'.format(1),
    ).first()

    assert schedule.func == 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle'
    assert schedule.args == '1'

    invalid_configurations = data['import_settings_payload']
    invalid_configurations['import_settings'] = {}
    response = api_client.put(
        url,
        data=invalid_configurations,
        format='json'
    )
    assert response.status_code == 400

    response = json.loads(response.content)
    assert response['non_field_errors'] == ['Import Settings are required']

    response = api_client.put(
        url,
        data=data['invalid_mapping_settings'],
        format='json'
    )
    assert response.status_code == 400

    # Test with Import Fields put request
    add_import_code_fields_payload = data['import_code_fields_payload']
    response = api_client.put(
        url,
        data=add_import_code_fields_payload,
        format='json'
    )

    assert response.status_code == 200
    response = json.loads(response.content)
    assert dict_compare_keys(response, data['add_import_code_fields_response']) == [], 'import settings api returns a diff in the keys'

    # Test with Import Fields put request with data removed
    add_import_code_fields_payload = data['import_code_fields_payload']
    # removed "VENDOR" from the import_code_fields
    add_import_code_fields_payload['import_settings']['import_code_fields'] = ["JOB"]
    response = api_client.put(
        url,
        data=add_import_code_fields_payload,
        format='json'
    )

    assert response.status_code == 400
    response = json.loads(response.content)
    assert response['non_field_errors'] == ["Cannot change the code fields once they are imported"]

    # Test with categories import without code and then adding code
    ImportLog.update_or_create_in_progress_import_log('CATEGORY', 1)

    add_import_code_fields_payload = data['import_code_fields_payload']
    add_import_code_fields_payload['import_settings']['import_code_fields'] = ['ACCOUNT', 'JOB', 'VENDOR']
    response = api_client.put(
        url,
        data=add_import_code_fields_payload,
        format='json'
    )
    assert response.status_code == 400
    response = json.loads(response.content)
    assert response['non_field_errors'] == ["Cannot change the code fields once they are imported"]


def test_advanced_settings(api_client, test_connection):
    '''
    Test advanced settings
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('advanced-settings', kwargs={'workspace_id': workspace_id})

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    payload = {
        'expense_memo_structure': [
            'employee_email',
            'merchant',
            'purpose',
            'report_number',
            'expense_link'
        ],
        'schedule_is_enabled': False,
        'interval_hours': 12,
        'emails_selected': json.dumps([
            {
                'name': 'Shwetabh Kumar',
                'email': 'shwetabh.kumar@fylehq.com'
            },
            {
                'name': 'Netra Ballabh',
                'email': 'nilesh.p@fylehq.com'
            },
        ]),
        'auto_create_vendor': True,
        'sync_sage_300_to_fyle_payments': True
    }

    response = api_client.post(url, payload)

    assert response.status_code == 201
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number',
        'expense_link'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]
    assert response.data['auto_create_vendor'] == True
    assert response.data['sync_sage_300_to_fyle_payments'] == True

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number',
        'expense_link'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]

    del payload['expense_memo_structure']

    AdvancedSetting.objects.filter(workspace_id=workspace_id).first().delete()

    response = api_client.post(url, payload)

    assert response.status_code == 201
    assert response.data['expense_memo_structure'] == [
        'employee_email',
        'merchant',
        'purpose',
        'report_number'
    ]
    assert response.data['schedule_is_enabled'] is False
    assert response.data['emails_selected'] == [
        {
            'name': 'Shwetabh Kumar',
            'email': 'shwetabh.kumar@fylehq.com'
        },
        {
            'name': 'Netra Ballabh',
            'email': 'nilesh.p@fylehq.com'
        },
    ]


def test_get_workspace_admins(api_client, test_connection):
    '''
    Test get workspace admins
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse('admin', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    response = api_client.get(url)
    assert response.status_code == 200


def test_trigger_export(
    mocker,
    api_client,
    test_connection,
    create_temp_workspace,
    add_fyle_credentials,
    add_accounting_export_expenses,
    add_export_settings,
    add_import_settings
):
    """
    Test Export Trigger API
    """
    workspace_id = 1
    AccountingExportSummary.objects.create(workspace_id=workspace_id)
    AdvancedSetting.objects.create(workspace_id=workspace_id, schedule_is_enabled=False, emails_selected=[], emails_added=[], auto_create_vendor=False, sync_sage_300_to_fyle_payments=False)

    url = reverse('trigger-exports', kwargs={'workspace_id': 1})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    mocker.patch(
        'apps.sage300.exports.purchase_invoice.tasks.ExportPurchaseInvoice.trigger_export',
        return_value=None
    )

    mocker.patch(
        'apps.sage300.exports.direct_cost.tasks.ExportDirectCost.trigger_export',
        return_value=None
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=1, type='PURCHASE_INVOICE').first()
    assert accounting_export.status == 'EXPORT_QUEUED'

    response = api_client.post(url)
    assert response.status_code == 200


def test_ready_view(api_client, test_connection):
    '''
    Test ready view
    '''
    url = reverse(
        'ready'
    )

    response = api_client.get(url)

    assert response.status_code == 200


def test_import_code_field_view(db, mocker, create_temp_workspace, api_client, test_connection):
    """
    Test ImportCodeFieldView
    """
    workspace_id = 1
    url = reverse('import-code-fields-config', kwargs={'workspace_id': workspace_id})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    vendor_log = ImportLog.update_or_create_in_progress_import_log('MERCHANT', workspace_id)
    account_log = ImportLog.update_or_create_in_progress_import_log('CATEGORY', workspace_id)
    job_log = ImportLog.update_or_create_in_progress_import_log('PROJECT', workspace_id)

    with mocker.patch('django.db.models.signals.post_save.send'):
        # Create MappingSetting object with the signal mocked
        MappingSetting.objects.create(
            workspace_id=workspace_id,
            source_field='PROJECT',
            destination_field='JOB',
            import_to_fyle=True,
            is_custom=False
        )

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'JOB': False,
        'VENDOR': False,
        'ACCOUNT': False
    }

    job_log.delete()

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'JOB': True,
        'VENDOR': False,
        'ACCOUNT': False
    }

    vendor_log.delete()
    account_log.delete()

    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == {
        'JOB': True,
        'VENDOR': True,
        'ACCOUNT': True
    }


def test_sage300_health_check_view(db, mocker, api_client, test_connection, create_temp_workspace, add_sage300_creds):
    """
    Test Sage300 health check view
    """
    workspace_id = 1
    url = f'/api/workspaces/{workspace_id}/token_health/'
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))

    # Test case 1: No credentials found
    Sage300Credential.objects.filter(workspace_id=workspace_id).delete()
    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Sage300 credentials not found'

    # Test case 2: Credentials expired
    sage300_creds = Sage300Credential.objects.create(
        identifier='test_identifier',
        username='test_username',
        password='test_password',
        api_key='test_api_key',
        api_secret='test_api_secret',
        workspace_id=workspace_id,
        is_expired=True
    )
    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Sage300 connection expired'

    # Test case 3: Connection healthy (cache hit)
    sage300_creds.is_expired = False
    sage300_creds.save()

    # Mock cache to return True (healthy) - this should skip the connection test
    cache_mock = mocker.patch('apps.workspaces.views.cache')
    cache_mock.get.return_value = True

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['message'] == 'Sage300 connection is active'

    # Test case 4: Connection healthy (cache miss, successful connection)
    # Mock cache to return None (cache miss)
    cache_mock.get.return_value = None
    cache_mock.set.return_value = None

    # Mock the SageDesktopConnector
    mock_connector = mocker.MagicMock()
    mocker.patch('apps.workspaces.views.SageDesktopConnector', return_value=mock_connector)

    # Mock successful connection test
    mock_connector.connection.vendors.get_vendor_types.return_value = ['type1', 'type2']

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['message'] == 'Sage300 connection is active'

    # Test case 5: Connection fails due to InvalidUserCredentials
    mock_connector.connection.vendors.get_vendor_types.side_effect = InvalidUserCredentials('Connection failed')
    mocker.patch('apps.workspaces.views.invalidate_sage300_credentials')

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Sage300 connection expired'

    # Test case 6: Connection fails due to other exception
    mock_connector.connection.vendors.get_vendor_types.side_effect = Exception('Connection failed')

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Something went wrong'


def test_feature_config_get_feature_config(db, mocker, create_temp_workspace, add_feature_config):
    """
    Test FeatureConfig.get_feature_config method for cache hit and cache miss scenarios
    """
    workspace_id = 1

    cache_mock = mocker.patch('apps.workspaces.models.cache')
    cache_mock.get.return_value = None
    result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')

    assert result == True
    cache_mock.get.assert_called_once()
    cache_mock.set.assert_called_once()

    cache_mock.reset_mock()
    cache_mock.get.return_value = False

    result = FeatureConfig.get_feature_config(workspace_id, 'fyle_webhook_sync_enabled')
    assert result == False
    cache_mock.get.assert_called_once()
    cache_mock.set.assert_not_called()
