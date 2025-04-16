from .fixtures import fixtures as data
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework import status
from apps.fyle.tasks import (
    update_non_exported_expenses, import_expenses
)
from apps.fyle.models import Expense
from apps.workspaces.models import Workspace
from apps.accounting_exports.models import AccountingExport


def test_update_non_exported_expenses(db, create_temp_workspace, mocker, api_client):
    expense = data['raw_expense']
    default_raw_expense = data['default_raw_expense']
    org_id = expense['org_id']
    payload = {
        "resource": "EXPENSE",
        "action": 'UPDATED_AFTER_APPROVAL',
        "data": expense,
        "reason": 'expense update testing',
    }

    expense_created, _ = Expense.objects.update_or_create(
        org_id=org_id,
        expense_id='txhJLOSKs1iN',
        workspace_id=1,
        defaults=default_raw_expense
    )
    expense_created.accounting_export_summary = {}
    expense_created.save()

    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=1,
        type='PURCHASE_INVOICE',
        status='EXPORT_READY'
    )
    accounting_export.expenses.add(expense_created)
    accounting_export.save()

    workspace = Workspace.objects.filter(id=1).first()
    workspace.org_id = org_id
    workspace.save()

    assert expense_created.category == 'Old Category'

    update_non_exported_expenses(payload['data'])

    expense = Expense.objects.get(expense_id='txhJLOSKs1iN', org_id=org_id)
    assert expense.category == 'ABN Withholding'

    accounting_export.status = 'COMPLETE'
    accounting_export.save()
    expense.category = 'Old Category'
    expense.save()

    update_non_exported_expenses(payload['data'])
    expense = Expense.objects.get(expense_id='txhJLOSKs1iN', org_id=org_id)
    assert expense.category == 'Old Category'

    try:
        update_non_exported_expenses(payload['data'])
    except ValidationError as e:
        assert e.detail[0] == 'Workspace mismatch'

    url = reverse('webhook-callback', kwargs={'workspace_id': 1})
    response = api_client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK

    url = reverse('webhook-callback', kwargs={'workspace_id': 2})
    response = api_client.post(url, data=payload, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_import_expenses(db, create_temp_workspace, add_accounting_export_expenses, add_export_settings, add_fyle_credentials, mocker, api_client, test_connection):
    """
    Test import_expenses
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=1).first()
    import_expenses(1, accounting_export_id=accounting_export.id, is_state_change_event=True, report_state='APPROVED', fund_source_key='PERSONAL')

    import_expenses(1, accounting_export_id=accounting_export.id, fund_source_key='PERSONAL')

    import_expenses(1, accounting_export_id=accounting_export.id, is_state_change_event=True, report_state='PAYMENT_PROCESSING', fund_source_key='PERSONAL')
