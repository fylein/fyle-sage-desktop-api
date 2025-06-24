import json
from django_q.models import Schedule
import pytest  # noqa
from django.urls import reverse
from fyle_accounting_mappings.models import MappingSetting

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import (
    Workspace,
    Sage300Credential,
    ExportSetting,
    AdvancedSetting
)
from fyle_integrations_imports.models import ImportLog
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
    Test post of sage300 creds
    '''
    Workspace.objects.all().delete()
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    url = reverse('sage300-creds', kwargs={'workspace_id': response.data['id']})

    payload = {
        'identifier': "indentifier",
        'password': "passeord",
        'username': "username",
        'workspace': response.data['id']
    }

    mocker.patch(
        'sage_desktop_sdk.core.client.Client.update_cookie',
        return_value={'text': {'Result': 2}}
    )

    response = api_client.post(url, payload)
    assert response.status_code == 201


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

    # Mock cache.get to return True (cache hit - healthy connection)
    mocker.patch('apps.workspaces.views.cache.get', return_value=True)

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['message'] == 'Sage300 connection is active'

    # Test case 4: Connection healthy (cache miss, successful connection)
    # Mock cache.get to return None (cache miss)
    mocker.patch('apps.workspaces.views.cache.get', return_value=None)
    mocker.patch('apps.workspaces.views.cache.set')
    
    # Mock timedelta since it's used in the view
    mocker.patch('apps.workspaces.views.timedelta')

    # Mock the SageDesktopConnector
    mock_connector = mocker.MagicMock()
    mocker.patch('apps.workspaces.views.SageDesktopConnector', return_value=mock_connector)

    # Mock successful connection test
    mock_connector.connection.vendors.get_vendor_types.return_value = ['type1', 'type2']

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data['message'] == 'Sage300 connection is active'

    # Test case 5: Connection fails
    mock_connector.connection.vendors.get_vendor_types.side_effect = Exception('Connection failed')
    mocker.patch('apps.workspaces.views.invalidate_sage300_credentials')

    response = api_client.get(url)
    assert response.status_code == 400
    assert response.data['message'] == 'Sage300 connection expired'
