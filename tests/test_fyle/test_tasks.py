from .fixtures import fixtures as data
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework import status
from apps.fyle.tasks import (
    re_run_skip_export_rule, update_non_exported_expenses, import_expenses
)
from apps.fyle.models import Expense, ExpenseFilter
from apps.workspaces.models import Workspace
from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error


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


def test_re_run_skip_export_rule(db, create_temp_workspace, mocker, api_client, test_connection, add_export_settings):
    """Test the re-running of skip export rules for expenses

    This test verifies that expenses are correctly skipped based on email filters,
    expense groups are properly cleaned up, and export details are updated.
    """
    # Create an expense filter that will match expenses with employee_email 'jhonsnow@fyle.in'
    ExpenseFilter.objects.create(
        workspace_id=1,
        condition='expense_number',
        operator='in',
        values=['expense_1'],
        rank=1,
        join_by=None,
    )

    # Retrieve test expenses data and modify them to ensure unique grouping
    expenses = list(data["expenses_spent_at"])
    expenses[0].update({
        'expense_number': 'expense_1',
        'employee_email': 'jhonsnow@fyle.in',
        'report_id': 'report_1',
        'claim_number': 'claim_1',
        'fund_source': 'PERSONAL'
    })
    expenses[1].update({
        'expense_number': 'expense_2',
        'employee_email': 'other.email@fyle.in',
        'report_id': 'report_2',
        'claim_number': 'claim_2',
        'fund_source': 'PERSONAL'
    })
    expenses[2].update({
        'expense_number': 'expense_3',
        'employee_email': 'anish@fyle.in',
        'report_id': 'report_3',
        'claim_number': 'claim_3',
        'fund_source': 'PERSONAL',
        'amount': 1000
    })
    # Assign org_id to all expenses
    for expense in expenses:
        expense['org_id'] = 'riseabovehate1'

    # Create expense objects in the database
    expense_objects = Expense.create_expense_objects(expenses, 1)

    # Mark all expenses as failed exports by updating their accounting_export_summary
    for expense in Expense.objects.filter(workspace_id=1):
        expense.accounting_export_summary = {
            'state': 'FAILED',
            'synced': False
        }
        expense.save()

    # Create expense groups - this should create 3 separate groups, one for each expense
    AccountingExport.create_accounting_export(expense_objects, fund_source="PERSONAL", workspace_id=1)
    expense_groups = AccountingExport.objects.filter(workspace_id=1)
    accounting_export_ids = expense_groups.values_list('id', flat=True)
    accounting_export_skipped = AccountingExport.objects.filter(workspace_id=1, expenses__expense_id=expenses[0]['id']).first()

    # Create TaskLog to simulate in-progress export
    # get the first expense group id, and create a task log for it
    accounting_export = AccountingExport.objects.filter(workspace_id=1, expenses__expense_id=expenses[0]['id']).first()
    accounting_export.status = 'FAILED'
    accounting_export.save()

    # Create error for the first expense group
    error = Error.objects.create(
        workspace_id=1,
        type='QBO_ERROR',
        error_title='Test error title',
        error_detail='Test error detail',
        accounting_export=AccountingExport.objects.get(id=accounting_export_skipped.id)
    )

    AccountingExportSummary.objects.update_or_create(
        workspace_id=1,
        defaults={
            'total_accounting_export_count': len(expense_groups),
            'failed_accounting_export_count': 1,
            'export_mode': 'MANUAL'
        }
    )

    workspace = Workspace.objects.get(id=1)

    assert accounting_export.status == 'FAILED'
    assert error.type == 'QBO_ERROR'

    re_run_skip_export_rule(workspace)

    # Test 1: Verify expense skipping based on email filter
    skipped_expense = Expense.objects.get(expense_number='expense_1')
    non_skipped_expense = Expense.objects.get(expense_number='expense_2')
    assert skipped_expense.is_skipped == True
    assert non_skipped_expense.is_skipped == False

    # Test 2: Verify expense group modifications 
    remaining_groups = AccountingExport.objects.filter(id__in=accounting_export_ids)
    assert remaining_groups.count() == 2

    # Test 3: Verify cleanup of task logs
    accounting_export = AccountingExport.objects.filter(workspace_id=1, id=accounting_export.id).first()
    assert accounting_export is None

    # Test 4: Verify cleanup of errors
    error = Error.objects.filter(workspace_id=1, accounting_export_id=accounting_export_skipped.id).first()
    assert error is None

    # Test 5: Verify LastExportDetail updates
    last_export_detail = AccountingExportSummary.objects.filter(workspace_id=1).first()
    assert last_export_detail.failed_accounting_export_count == 0
