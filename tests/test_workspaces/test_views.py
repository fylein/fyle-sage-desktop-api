import json
import pytest  # noqa
from django.urls import reverse
from apps.workspaces.models import (
    Workspace,
    Sage300Credential,
    ExportSetting,
    ImportSetting,
    AdvancedSetting
)


def test_post_of_workspace(api_client, test_connection):
    '''
    Test post of workspace
    '''
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
        'credit_card_expense_export_type': 'JOURNAL_ENTRY',
        'credit_card_expense_state': 'PAID',
        'credit_card_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_date': 'CREATED_AT',
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
    assert export_settings.credit_card_expense_export_type == 'JOURNAL_ENTRY'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'CREATED_AT'
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
    assert export_settings.credit_card_expense_export_type == 'JOURNAL_ENTRY'
    assert export_settings.credit_card_expense_state == 'PAID'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'CREATED_AT'
    assert export_settings.default_reimbursable_account_name == 'reimbursable account'
    assert export_settings.default_reimbursable_account_id == '123'
    assert export_settings.default_ccc_credit_card_account_name == 'CCC credit card account'
    assert export_settings.default_ccc_credit_card_account_id == '123'
    assert export_settings.default_reimbursable_credit_card_account_name == 'reimbursable credit card account'
    assert export_settings.default_reimbursable_credit_card_account_id == '342'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'


def test_import_settings(api_client, test_connection):
    '''
    Test export settings
    '''
    url = reverse('workspaces')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)
    workspace_id = response.data['id']
    url = reverse(
        'import-settings',
        kwargs={'workspace_id': workspace_id}
    )

    payload = {
        'import_categories': True,
        'import_vendors_as_merchants': True
    }
    response = api_client.post(url, payload)
    import_settings = ImportSetting.objects.filter(workspace_id=workspace_id).first()
    assert response.status_code == 201
    assert import_settings.import_categories is True
    assert import_settings.import_vendors_as_merchants is True

    response = api_client.get(url)
    assert response.status_code == 200
    assert import_settings.import_categories is True
    assert import_settings.import_vendors_as_merchants is True


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
