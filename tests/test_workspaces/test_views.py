import json

from django.urls import reverse
import pytest       # noqa

from apps.workspaces.models import Workspace, ExportSettings


def test_post_of_workspace(api_client, test_connection):
    '''
    Test post of workspace
    '''
    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace = Workspace.objects.filter(org_id='orNoatdUnm1w').first()

    assert response.status_code == 201
    assert workspace.name == response.data['name']
    assert workspace.org_id == response.data['org_id']
    assert workspace.currency == response.data['currency']

    response = json.loads(response.content)

    response = api_client.post(url)
    assert response.status_code == 201


def test_get_of_workspace(api_client, test_connection):
    '''
    Test get of workspace
    '''
    url = reverse(
        'workspaces'
    )

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
    assert response.data['currency'] == 'USD'


def test_export_settings(api_client, test_connection):
    '''
    Test export settings
    '''
    url = reverse(
        'workspaces'
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    workspace_id = response.data['id']

    url = reverse(
        'export-settings', kwargs={
            'workspace_id': workspace_id
        }
    )

    api_client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(test_connection.access_token))
    response = api_client.post(url)

    assert response.status_code == 400

    payload = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'reimbursable_expense_state': 'PAYMENT_PROCESSING',
        'reimbursable_expense_date': 'last_spent_at',
        'reimbursable_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_state':  'CLOSED',
        'credit_card_expense_grouped_by': 'EXPENSE',
        'credit_card_expense_date': 'created_at',
        'default_ccc_account_name': 'credit card account',
        'default_ccc_account_id': '12312',
        'default_vendor_name': 'Nilesh',
        'default_vendor_id': '123'
    }

    response = api_client.post(url, payload)

    export_settings = ExportSettings.objects.filter(workspace_id=workspace_id).first()

    assert response.status_code == 201
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'last_spent_at'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'PURCHASE_INVOICE'
    assert export_settings.credit_card_expense_state == 'CLOSED'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'created_at'
    assert export_settings.default_credit_card_account_name == 'credit card account'
    assert export_settings.default_credit_card_account_id == '12312'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'

    response = api_client.get(url)

    assert response.status_code == 200
    assert export_settings.reimbursable_expenses_export_type == 'PURCHASE_INVOICE'
    assert export_settings.reimbursable_expense_state == 'PAYMENT_PROCESSING'
    assert export_settings.reimbursable_expense_date == 'last_spent_at'
    assert export_settings.reimbursable_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_export_type == 'PURCHASE_INVOICE'
    assert export_settings.credit_card_expense_state == 'CLOSED'
    assert export_settings.credit_card_expense_grouped_by == 'EXPENSE'
    assert export_settings.credit_card_expense_date == 'created_at'
    assert export_settings.default_credit_card_account_name == 'credit card account'
    assert export_settings.default_credit_card_account_id == '12312'
    assert export_settings.default_vendor_name == 'Nilesh'
    assert export_settings.default_vendor_id == '123'
