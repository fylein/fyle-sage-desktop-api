from datetime import datetime, timezone

from django.urls import reverse
from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.fyle.models import Expense, ExpenseFilter
from apps.fyle.tasks import (
    _delete_accounting_exports_for_report,
    _handle_expense_ejected_from_report,
    cleanup_scheduled_task,
    delete_accounting_export_and_related_data,
    handle_category_changes_for_expense,
    handle_expense_fund_source_change,
    handle_expense_report_change,
    handle_fund_source_changes_for_expense_ids,
    handle_org_setting_updated,
    import_expenses,
    process_accounting_export_for_fund_source_update,
    re_run_skip_export_rule,
    recreate_accounting_exports,
    schedule_task_for_expense_group_fund_source_change,
    update_non_exported_expenses,
)
from apps.workspaces.models import ExportSetting, Workspace
from tests.test_fyle.fixtures import fixtures as data
from tests.test_fyle.fixtures import fixtures as fyle_fixtures


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


def test_import_expenses(db, create_temp_workspace, add_accounting_export_expenses, add_export_settings, add_fyle_credentials, mocker, api_client, test_connection, add_advanced_settings, add_accounting_export_summary):
    """
    Test import_expenses
    """
    mocker.patch(
        'fyle_integrations_platform_connector.apis.Expenses.get',
        return_value=data['expenses']
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=1).first()
    import_expenses(1, accounting_export_id=accounting_export.id, is_state_change_event=True, report_state='APPROVED', fund_source_key='PERSONAL', trigger_export=True, triggered_by=ExpenseImportSourceEnum.WEBHOOK)

    import_expenses(1, accounting_export_id=accounting_export.id, fund_source_key='PERSONAL')

    import_expenses(1, accounting_export_id=accounting_export.id, is_state_change_event=True, report_state='PAYMENT_PROCESSING', fund_source_key='PERSONAL', trigger_export=True, triggered_by=ExpenseImportSourceEnum.WEBHOOK)


def test_re_run_skip_export_rule(db, create_temp_workspace, mocker, api_client, add_export_settings):
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
        type='SAGE300_ERROR',
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
    assert error.type == 'SAGE300_ERROR'

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

    try:
        ExpenseFilter.objects.create(
            workspace_id=2,
            condition='last_spend_at',
            operator='in',
            values=['2025-04-29'],
            rank=1,
            join_by=None,
        )
    except ValidationError as e:
        assert e.detail[0] == 'Failed to process expense filter'


def test_handle_expense_fund_source_change_no_changes(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test handle_expense_fund_source_change when no fund source changes are detected
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Mock platform connector
    mock_platform_connector = mocker.patch('apps.fyle.tasks.PlatformConnector')
    mock_platform_instance = mock_platform_connector.return_value

    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    mock_platform_instance.expenses.get.return_value = fund_source_expenses

    # Create matching expenses in DB (no changes)
    Expense.create_expense_objects(fund_source_expenses, workspace_id)

    # Mock the handler function
    mock_handle_changes = mocker.patch('apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')

    handle_expense_fund_source_change(workspace_id, report_id, mock_platform_instance)

    # Should not call the handler since no changes detected
    mock_handle_changes.assert_not_called()


def test_handle_expense_fund_source_change_with_changes(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test handle_expense_fund_source_change when fund source changes are detected
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Mock platform connector
    mock_platform_connector = mocker.patch('apps.fyle.tasks.PlatformConnector')
    mock_platform_instance = mock_platform_connector.return_value

    # Create original expenses in DB
    original_expenses = fyle_fixtures['fund_source_change_expenses']
    Expense.create_expense_objects(original_expenses, workspace_id)

    # Mock platform to return expenses with fund source changes
    updated_expenses = fyle_fixtures['updated_fund_source_expenses']
    mock_platform_instance.expenses.get.return_value = updated_expenses

    # Mock the handler function
    mock_handle_changes = mocker.patch('apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')

    handle_expense_fund_source_change(workspace_id, report_id, mock_platform_instance)

    # Should call the handler with changed expense IDs
    mock_handle_changes.assert_called_once()
    call_args = mock_handle_changes.call_args[1]
    assert call_args['workspace_id'] == workspace_id
    assert call_args['report_id'] == report_id
    assert len(call_args['changed_expense_ids']) == 1  # Only txFundSource1 changed
    assert 'PERSONAL' in call_args['affected_fund_source_expense_ids']
    assert 'CCC' in call_args['affected_fund_source_expense_ids']


def test_handle_fund_source_changes_for_expense_ids_all_processed(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses,
    mocker
):
    """
    Test handle_fund_source_changes_for_expense_ids when all accounting exports can be processed immediately
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting exports in EXPORT_READY state
    personal_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']
    ccc_expenses = [exp for exp in expense_objects if exp.fund_source == 'CCC']

    if personal_expenses:
        AccountingExport.create_accounting_export(
            personal_expenses,
            fund_source='PERSONAL',
            workspace_id=workspace_id
        )

    if ccc_expenses:
        AccountingExport.create_accounting_export(
            ccc_expenses,
            fund_source='CCC',
            workspace_id=workspace_id
        )

    # Mock dependencies
    mock_recreate = mocker.patch('apps.fyle.tasks.recreate_accounting_exports')
    mock_cleanup = mocker.patch('apps.fyle.tasks.cleanup_scheduled_task')
    mock_schedule = mocker.patch('apps.fyle.tasks.schedule_task_for_expense_group_fund_source_change')

    affected_fund_source_expense_ids = {
        'PERSONAL': [expense_ids[0]],
        'CCC': [expense_ids[1]]
    }

    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should recreate accounting exports, not schedule
    mock_recreate.assert_called_once()
    call_kwargs = mock_recreate.call_args[1]
    assert call_kwargs['workspace_id'] == workspace_id
    assert set(call_kwargs['expense_ids']) == set(expense_ids)
    # cleanup_scheduled_task is not called because task_name is None
    mock_cleanup.assert_not_called()
    mock_schedule.assert_not_called()


def test_handle_fund_source_changes_for_expense_ids_some_skipped(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses,
    mocker
):
    """
    Test handle_fund_source_changes_for_expense_ids when some accounting exports need to be skipped
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting exports - one in EXPORT_READY, one in IN_PROGRESS
    personal_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']
    ccc_expenses = [exp for exp in expense_objects if exp.fund_source == 'CCC']

    if personal_expenses:
        AccountingExport.create_accounting_export(
            personal_expenses,
            fund_source='PERSONAL',
            workspace_id=workspace_id
        )

        if ccc_expenses:
            AccountingExport.create_accounting_export(
                ccc_expenses,
                fund_source='CCC',
                workspace_id=workspace_id
            )
            # Set one to IN_PROGRESS status - this should cause the function to schedule a retry
            accounting_export_ccc = AccountingExport.objects.filter(
                workspace_id=workspace_id, fund_source='CCC'
            ).first()
            # Manually add the CCC expenses to the accounting export
            accounting_export_ccc.expenses.add(*ccc_expenses)
            accounting_export_ccc.status = 'IN_PROGRESS'
            accounting_export_ccc.save()

    # Mock dependencies
    mock_recreate = mocker.patch('apps.fyle.tasks.recreate_accounting_exports')
    mock_cleanup = mocker.patch('apps.fyle.tasks.cleanup_scheduled_task')
    mock_schedule = mocker.patch('apps.fyle.tasks.schedule_task_for_expense_group_fund_source_change')

    affected_fund_source_expense_ids = {
        'PERSONAL': [expense_ids[0]],
        'CCC': [expense_ids[1]]
    }

    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should schedule retry instead of recreating
    mock_schedule.assert_called_once()
    mock_recreate.assert_not_called()
    mock_cleanup.assert_not_called()


def test_process_accounting_export_for_fund_source_update_export_ready(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test process_accounting_export_for_fund_source_update with EXPORT_READY status
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses'][:1]  # Just one expense
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting export in EXPORT_READY state
    AccountingExport.create_accounting_export(
        expense_objects,
        fund_source='PERSONAL',
        workspace_id=workspace_id
    )
    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id, fund_source='PERSONAL'
    ).first()

    # Mock delete function
    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    affected_fund_source_expense_ids = {'PERSONAL': expense_ids}

    result = process_accounting_export_for_fund_source_update(
        accounting_export=accounting_export,
        changed_expense_ids=expense_ids,
        workspace_id=workspace_id,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should process and delete the accounting export
    assert result is True
    mock_delete.assert_called_once_with(accounting_export=accounting_export, workspace_id=workspace_id)


def test_process_accounting_export_for_fund_source_update_in_progress(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test process_accounting_export_for_fund_source_update with IN_PROGRESS status
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses'][:1]
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting export in IN_PROGRESS state
    AccountingExport.create_accounting_export(
        expense_objects,
        fund_source='PERSONAL',
        workspace_id=workspace_id
    )
    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id, fund_source='PERSONAL'
    ).first()
    accounting_export.status = 'IN_PROGRESS'
    accounting_export.save()

    # Mock delete function
    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    affected_fund_source_expense_ids = {'PERSONAL': expense_ids}

    result = process_accounting_export_for_fund_source_update(
        accounting_export=accounting_export,
        changed_expense_ids=expense_ids,
        workspace_id=workspace_id,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should skip processing
    assert result is False
    mock_delete.assert_not_called()


def test_process_accounting_export_for_fund_source_update_already_exported(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test process_accounting_export_for_fund_source_update with already exported accounting export
    """

    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses'][:1]
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting export that's already exported
    AccountingExport.create_accounting_export(
        expense_objects,
        fund_source='PERSONAL',
        workspace_id=workspace_id
    )
    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id, fund_source='PERSONAL'
    ).first()
    accounting_export.exported_at = datetime.now(timezone.utc)
    accounting_export.save()

    # Mock delete function
    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    affected_fund_source_expense_ids = {'PERSONAL': expense_ids}

    result = process_accounting_export_for_fund_source_update(
        accounting_export=accounting_export,
        changed_expense_ids=expense_ids,
        workspace_id=workspace_id,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should skip processing
    assert result is False
    mock_delete.assert_not_called()


def test_delete_accounting_export_and_related_data(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses
):
    """
    Test delete_accounting_export_and_related_data function
    """

    workspace_id = 1

    # Get existing accounting export from fixture
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    # Create an error for this accounting export
    error = Error.objects.create(
        workspace_id=workspace_id,
        type='SAGE300_ERROR',
        error_title='Test error',
        error_detail='Test error detail',
        accounting_export=accounting_export
    )

    # Verify initial state
    assert AccountingExport.objects.filter(id=accounting_export.id).exists()
    assert Error.objects.filter(id=error.id).exists()

    delete_accounting_export_and_related_data(accounting_export, workspace_id)

    # Verify accounting export and related error are deleted
    assert not AccountingExport.objects.filter(id=accounting_export.id).exists()
    assert not Error.objects.filter(id=error.id).exists()


def test_recreate_accounting_exports(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test recreate_accounting_exports function
    """
    workspace_id = 1

    # Enable both reimbursable and credit card exports
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.save()

    # Create test expenses with mixed fund sources
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Mock expense filtering functions
    mock_get_filtered_expenses = mocker.patch('apps.fyle.tasks.get_filtered_expenses')
    mock_get_filtered_expenses.return_value = expense_objects

    # Mock AccountingExport.create_accounting_export
    mock_create_export = mocker.patch.object(AccountingExport, 'create_accounting_export')

    recreate_accounting_exports(workspace_id, expense_ids)

    # Should call create_accounting_export for both PERSONAL and CCC expenses
    assert mock_create_export.call_count == 2

    # Verify the calls
    call_args_list = mock_create_export.call_args_list
    fund_sources_called = [call[1]['fund_source'] for call in call_args_list]
    assert 'PERSONAL' in fund_sources_called
    assert 'CCC' in fund_sources_called


def test_schedule_task_for_expense_group_fund_source_change(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test schedule_task_for_expense_group_fund_source_change function
    """

    workspace_id = 1
    changed_expense_ids = [1, 2, 3]
    report_id = 'rpTest123'
    affected_fund_source_expense_ids = {'PERSONAL': [1, 2], 'CCC': [3]}

    # Mock django-q schedule function
    mock_schedule_function = mocker.patch('apps.fyle.tasks.schedule')

    schedule_task_for_expense_group_fund_source_change(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Verify schedule was called with correct parameters
    mock_schedule_function.assert_called_once()
    call_args = mock_schedule_function.call_args[0]  # positional args
    call_kwargs = mock_schedule_function.call_args[1]  # keyword args

    # Check positional arguments
    assert call_args[0] == 'apps.fyle.tasks.handle_fund_source_changes_for_expense_ids'
    assert call_args[1] == workspace_id
    assert call_args[2] == changed_expense_ids
    assert call_args[3] == report_id
    assert call_args[4] == affected_fund_source_expense_ids

    # Check keyword arguments
    assert call_kwargs['repeats'] == 10
    assert call_kwargs['schedule_type'] == 'M'
    assert call_kwargs['minutes'] == 5
    assert 'name' in call_kwargs


def test_cleanup_scheduled_task(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test cleanup_scheduled_task function
    """

    workspace_id = 1
    task_name = 'test_task_123'

    # Create a mock schedule
    mock_schedule = mocker.Mock()
    mock_schedule_filter = mocker.patch.object(Schedule.objects, 'filter')
    mock_schedule_filter.return_value.first.return_value = mock_schedule

    cleanup_scheduled_task(task_name, workspace_id)

    # Verify schedule was queried and deleted
    mock_schedule_filter.assert_called_once_with(name=task_name, func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')
    mock_schedule.delete.assert_called_once()


def test_update_non_exported_expenses_fund_source_change(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test update_non_exported_expenses with fund source change detection
    """

    # Setup test data
    original_expense_data = fyle_fixtures['fund_source_change_expenses'][0]
    updated_expense_data = fyle_fixtures['updated_fund_source_expenses'][0]

    org_id = original_expense_data['org_id']
    workspace_id = 1

    # Create workspace with correct org_id
    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_id = org_id
    workspace.save()

    # Create original expense in DB
    expense_created, _ = Expense.objects.update_or_create(
        org_id=org_id,
        expense_id=original_expense_data['id'],
        workspace_id=workspace_id,
        defaults={
            'fund_source': original_expense_data['fund_source'],
            'category': original_expense_data['category'],
            'amount': original_expense_data['amount'],
            'currency': original_expense_data['currency'],
            'employee_email': original_expense_data['employee_email'],
            'report_id': original_expense_data['report_id']
        }
    )

    # Create an accounting export for this expense so it can be processed
    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source=original_expense_data['fund_source'],
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense_created)

    # Mock the fund source change handler
    mock_handle_changes = mocker.patch('apps.fyle.tasks.handle_fund_source_changes_for_expense_ids')

    # Mock FyleExpenses constructor to avoid complex field requirements
    mock_fyle_expenses = mocker.patch('apps.fyle.tasks.FyleExpenses.construct_expense_object')
    mock_fyle_expenses.return_value = [{
        'source_account_type': updated_expense_data['source_account_type'],
        'category': updated_expense_data['category'],
        'sub_category': updated_expense_data.get('sub_category')
    }]

    # Mock Expense.create_expense_objects to simulate expense update
    mock_create_expense = mocker.patch('apps.fyle.tasks.Expense.create_expense_objects')

    # Mock the expense update to actually update the fund_source in the database
    def mock_update_expense(expense_objects, workspace_id, skip_update=False):
        # Update the expense in the database to simulate the fund source change
        expense_created.fund_source = updated_expense_data['fund_source']
        expense_created.save()

    mock_create_expense.side_effect = mock_update_expense

    # Update expense with fund source change
    update_non_exported_expenses(updated_expense_data)

    # Verify expense was updated
    updated_expense = Expense.objects.get(expense_id=original_expense_data['id'], org_id=org_id)
    assert updated_expense.fund_source == updated_expense_data['fund_source']

    # Verify fund source change handler was called
    mock_handle_changes.assert_called_once()
    call_args = mock_handle_changes.call_args[1]
    assert call_args['workspace_id'] == workspace_id
    assert call_args['report_id'] == original_expense_data['report_id']
    assert updated_expense.id in call_args['changed_expense_ids']


def test_import_expenses_fund_source_change_exception(
    db,
    create_temp_workspace,
    add_export_settings,
    add_fyle_credentials,
    mocker
):
    """
    Test import_expenses handles exception in fund source change detection
    """
    workspace_id = 1
    report_id = 'rpTest123'

    # Mock platform connector
    mock_platform_connector = mocker.patch('apps.fyle.tasks.PlatformConnector')
    mock_platform_instance = mock_platform_connector.return_value
    # Return some expenses so the fund source change logic gets executed
    mock_platform_instance.expenses.get.return_value = [{'id': 'tx123', 'report_id': report_id}]

    # Mock Expense.objects.filter for fund source check
    mock_expense_filter = mocker.patch('apps.fyle.tasks.Expense.objects.filter')
    # Set up the mock to return expenses for the specific report_id
    mock_queryset = mocker.Mock()
    mock_queryset.count.return_value = 1  # Has expenses for this report
    mock_expense_filter.return_value = mock_queryset

    # Mock handle_expense_fund_source_change to raise exception
    mock_handle_fund_source = mocker.patch('apps.fyle.tasks.handle_expense_fund_source_change')
    mock_handle_fund_source.side_effect = Exception("Test exception")

    # Mock Expense.create_expense_objects
    mock_create_expense = mocker.patch('apps.fyle.tasks.Expense.create_expense_objects')
    mock_create_expense.return_value = []

    # Mock other dependencies
    mock_expense_filter_queryset = mocker.Mock()
    mock_expense_filter_queryset.order_by.return_value = []
    mocker.patch('apps.fyle.tasks.ExpenseFilter.objects.filter').return_value = mock_expense_filter_queryset
    mocker.patch('apps.fyle.tasks.AccountingExport.create_accounting_export')
    mocker.patch('apps.fyle.tasks.filter_expenses_based_on_state').return_value = [{'id': 'tx123', 'report_id': report_id}]
    mocker.patch('apps.fyle.tasks.get_expense_import_states').return_value = ['APPROVED']
    mocker.patch('apps.fyle.tasks.get_source_account_types_based_on_export_modules').return_value = ['PERSONAL_CASH_ACCOUNT']
    # Mock transaction.atomic as a context manager
    mock_atomic = mocker.patch('apps.fyle.tasks.transaction.atomic')
    mock_atomic.return_value.__enter__ = mocker.Mock()
    mock_atomic.return_value.__exit__ = mocker.Mock(return_value=None)

    # Call import_expenses with state change event
    import_expenses(
        workspace_id=workspace_id,
        is_state_change_event=True,
        report_id=report_id,
        report_state='APPROVED'
    )

    # Verify exception was handled gracefully (should not crash the function)
    mock_handle_fund_source.assert_called_once()


def test_import_expenses_no_expenses_for_fund_source_check(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test import_expenses when no expenses exist for fund source check
    """
    workspace_id = 1
    report_id = 'rpTest123'

    # Mock platform connector
    mock_platform_connector = mocker.patch('apps.fyle.tasks.PlatformConnector')
    mock_platform_instance = mock_platform_connector.return_value
    mock_platform_instance.expenses.get.return_value = []

    # Mock Expense.objects.filter to return 0 count
    mock_expense_filter = mocker.patch('apps.fyle.tasks.Expense.objects.filter')
    mock_expense_filter.return_value.count.return_value = 0

    # Mock handle_expense_fund_source_change
    mock_handle_fund_source = mocker.patch('apps.fyle.tasks.handle_expense_fund_source_change')

    # Mock other dependencies
    mock_create_expense = mocker.patch('apps.fyle.tasks.Expense.create_expense_objects')
    mock_create_expense.return_value = []
    mocker.patch('apps.fyle.tasks.ExpenseFilter.objects.filter').return_value = []
    mocker.patch('apps.fyle.tasks.AccountingExport.create_accounting_export')

    # Call import_expenses with state change event
    import_expenses(
        workspace_id=workspace_id,
        is_state_change_event=True,
        report_id=report_id,
        report_state='APPROVED'
    )

    # Verify fund source change was not called due to no expenses
    mock_handle_fund_source.assert_not_called()


def test_handle_fund_source_changes_no_affected_exports(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test handle_fund_source_changes_for_expense_ids when no affected exports found
    """
    workspace_id = 1
    changed_expense_ids = [1, 2, 3]
    report_id = 'rpTest123'
    affected_fund_source_expense_ids = {'PERSONAL': [1], 'CCC': [2, 3]}

    # Mock construct_filter_for_affected_accounting_exports
    mock_construct_filter = mocker.patch('apps.fyle.tasks.construct_filter_for_affected_accounting_exports')
    mock_filter = mocker.Mock()
    mock_construct_filter.return_value = mock_filter

    # Mock AccountingExport.objects.filter to return empty queryset
    mock_accounting_export_filter = mocker.patch('apps.fyle.tasks.AccountingExport.objects.filter')
    mock_queryset = mocker.Mock()
    mock_queryset.annotate.return_value.distinct.return_value = []  # Empty queryset after annotate/distinct
    mock_accounting_export_filter.return_value = mock_queryset

    # Mock get_logger
    mock_get_logger = mocker.patch('apps.fyle.tasks.get_logger')
    mock_logger = mocker.Mock()
    mock_get_logger.return_value = mock_logger

    # Call the function
    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Verify that it logs and returns early
    mock_logger.info.assert_called_with(
        "No accounting exports found for changed expenses: %s in workspace %s",
        changed_expense_ids,
        workspace_id
    )


def test_handle_fund_source_changes_with_task_name_cleanup(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test handle_fund_source_changes_for_expense_ids with task_name cleanup
    """
    workspace_id = 1
    expense_ids = [5, 6]
    report_id = 'rpFundTest123'
    task_name = 'test_task_cleanup'
    affected_fund_source_expense_ids = {'PERSONAL': [5], 'CCC': [6]}

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)

    # Create accounting exports in EXPORT_READY state (can be processed)
    personal_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']
    ccc_expenses = [exp for exp in expense_objects if exp.fund_source == 'CCC']

    if personal_expenses:
        AccountingExport.create_accounting_export(
            personal_expenses,
            fund_source='PERSONAL',
            workspace_id=workspace_id
        )

    if ccc_expenses:
        AccountingExport.create_accounting_export(
            ccc_expenses,
            fund_source='CCC',
            workspace_id=workspace_id
        )

    # Mock functions
    mock_recreate = mocker.patch('apps.fyle.tasks.recreate_accounting_exports')
    mock_cleanup = mocker.patch('apps.fyle.tasks.cleanup_scheduled_task')
    mock_schedule = mocker.patch('apps.fyle.tasks.schedule_task_for_expense_group_fund_source_change')

    # Call the function with task_name
    handle_fund_source_changes_for_expense_ids(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids,
        task_name=task_name
    )

    # Should recreate accounting exports and cleanup task
    mock_recreate.assert_called_once()
    mock_cleanup.assert_called_once_with(task_name=task_name, workspace_id=workspace_id)
    mock_schedule.assert_not_called()


def test_process_accounting_export_complete_status(
    db,
    create_temp_workspace,
    add_export_settings
):
    """
    Test process_accounting_export_for_fund_source_update with COMPLETE status
    """
    workspace_id = 1

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    personal_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']

    # Create accounting export
    AccountingExport.create_accounting_export(
        personal_expenses,
        fund_source='PERSONAL',
        workspace_id=workspace_id
    )

    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()
    accounting_export.status = 'COMPLETE'
    accounting_export.save()

    # Call the function
    result = process_accounting_export_for_fund_source_update(
        accounting_export=accounting_export,
        changed_expense_ids=[1, 2],
        workspace_id=workspace_id,
        report_id='rpTest123',
        affected_fund_source_expense_ids={'PERSONAL': [1], 'CCC': [2]}
    )

    # Should return False (skipped)
    assert result is False


def test_recreate_accounting_exports_no_expenses(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test recreate_accounting_exports when no expenses found
    """
    workspace_id = 1
    expense_ids = [999, 998]  # Non-existent expense IDs

    # Mock logger
    mock_logger = mocker.patch('apps.fyle.tasks.logger')

    # Call the function
    recreate_accounting_exports(workspace_id, expense_ids)

    # Should log warning and return early
    mock_logger.warning.assert_called_with(
        "No expenses found for recreation: %s in workspace %s",
        expense_ids,
        workspace_id
    )


def test_recreate_accounting_exports_skip_reimbursable_expenses(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test recreate_accounting_exports skipping reimbursable expenses when not configured
    """
    workspace_id = 1

    # Disable reimbursable expenses export
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_export_type = None
    export_setting.save()

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Mock expense filtering functions
    mock_get_filtered_expenses = mocker.patch('apps.fyle.tasks.get_filtered_expenses')
    mock_get_filtered_expenses.return_value = expense_objects

    # Mock AccountingExport.create_accounting_export
    mocker.patch.object(AccountingExport, 'create_accounting_export')

    # Call the function
    recreate_accounting_exports(workspace_id, expense_ids)

    # Should skip reimbursable expenses and mark them as skipped
    personal_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']
    if personal_expenses:
        for exp in personal_expenses:
            exp.refresh_from_db()
            assert exp.is_skipped is True


def test_recreate_accounting_exports_skip_ccc_expenses(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test recreate_accounting_exports skipping CCC expenses when not configured
    """
    workspace_id = 1

    # Disable CCC expenses export (keep reimbursable enabled)
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.credit_card_expense_export_type = None
    export_setting.save()

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Mock expense filtering functions
    mock_get_filtered_expenses = mocker.patch('apps.fyle.tasks.get_filtered_expenses')
    mock_get_filtered_expenses.return_value = expense_objects

    # Mock AccountingExport.create_accounting_export
    mocker.patch.object(AccountingExport, 'create_accounting_export')

    # Call the function
    recreate_accounting_exports(workspace_id, expense_ids)

    # Should skip CCC expenses and mark them as skipped
    ccc_expenses = [exp for exp in expense_objects if exp.fund_source == 'CCC']
    if ccc_expenses:
        for exp in ccc_expenses:
            exp.refresh_from_db()
            assert exp.is_skipped is True


def test_recreate_accounting_exports_with_expense_filters(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test recreate_accounting_exports with expense filters
    """
    workspace_id = 1

    # Enable both fund sources
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.save()

    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create mock expense filters
    mock_filters = mocker.Mock()
    mock_expense_filter = mocker.patch('apps.fyle.tasks.ExpenseFilter.objects.filter')
    mock_expense_filter.return_value.order_by.return_value = [mock_filters]

    # Mock workspace and get_filtered_expenses
    mock_workspace = mocker.patch('apps.fyle.tasks.Workspace.objects.get')
    mock_workspace.return_value = mocker.Mock()

    mock_get_filtered_expenses = mocker.patch('apps.fyle.tasks.get_filtered_expenses')
    mock_get_filtered_expenses.return_value = expense_objects

    # Mock AccountingExport.create_accounting_export
    mocker.patch.object(AccountingExport, 'create_accounting_export')

    # Call the function
    recreate_accounting_exports(workspace_id, expense_ids)

    # Should call get_filtered_expenses when filters exist
    mock_get_filtered_expenses.assert_called_once()
    mock_workspace.assert_called_once_with(id=workspace_id)


def test_schedule_task_already_exists(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test schedule_task_for_expense_group_fund_source_change when task already exists
    """
    workspace_id = 1
    changed_expense_ids = [1, 2, 3]
    report_id = 'rpTest123'
    affected_fund_source_expense_ids = {'PERSONAL': [1], 'CCC': [2, 3]}

    # Mock existing schedule
    mock_existing_schedule = mocker.Mock()
    mock_schedule_filter = mocker.patch('apps.fyle.tasks.Schedule.objects.filter')
    mock_schedule_filter.return_value.first.return_value = mock_existing_schedule

    # Mock logger
    mock_logger = mocker.patch('apps.fyle.tasks.logger')

    # Call the function
    schedule_task_for_expense_group_fund_source_change(
        workspace_id=workspace_id,
        changed_expense_ids=changed_expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Should log and return early
    mock_logger.info.assert_called_with(
        "Task already scheduled for changed expense ids %s in workspace %s",
        changed_expense_ids,
        workspace_id
    )


def test_cleanup_scheduled_task_not_found(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test cleanup_scheduled_task when no task found
    """
    workspace_id = 1
    task_name = 'non_existent_task'

    # Mock Schedule.objects.filter to return None
    mock_schedule_filter = mocker.patch.object(Schedule.objects, 'filter')
    mock_schedule_filter.return_value.first.return_value = None

    # Mock logger
    mock_logger = mocker.patch('apps.fyle.tasks.logger')

    # Call the function
    cleanup_scheduled_task(task_name, workspace_id)

    # Should log that no task was found
    mock_logger.info.assert_called_with("No scheduled task found to clean up: %s", task_name)


def test_handle_expense_report_change_added_to_report(db, mocker, add_expense_report_data):
    """
    Test handle_expense_report_change with ADDED_TO_REPORT action
    """
    workspace = Workspace.objects.get(id=1)

    expense_data = {
        'id': 'tx1234567890',
        'org_id': workspace.org_id,
        'report_id': 'rp1234567890'
    }

    mock_delete = mocker.patch('apps.fyle.tasks._delete_accounting_exports_for_report')

    handle_expense_report_change(expense_data, 'ADDED_TO_REPORT')

    mock_delete.assert_called_once()
    args = mock_delete.call_args[0]
    assert args[0] == 'rp1234567890'
    assert args[1].id == workspace.id


def test_handle_expense_report_change_ejected_from_report(db, mocker, add_expense_report_data):
    """
    Test handle_expense_report_change with EJECTED_FROM_REPORT action
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_expense_report_data['expenses'][0]

    expense_data = {
        'id': expense.expense_id,
        'org_id': workspace.org_id,
        'report_id': expense.report_id
    }

    mock_handle = mocker.patch('apps.fyle.tasks._handle_expense_ejected_from_report')

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')

    mock_handle.assert_called_once()


def test_delete_accounting_exports_for_report_basic(db, mocker, add_expense_report_data):
    """
    Test _delete_accounting_exports_for_report deletes non-exported accounting exports
    """
    workspace = Workspace.objects.get(id=1)

    expense = add_expense_report_data['expenses'][0]
    report_id = expense.report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    _delete_accounting_exports_for_report(report_id, workspace)

    assert mock_delete.called


def test_delete_accounting_exports_for_report_no_expenses(db, mocker, create_temp_workspace):
    """
    Test _delete_accounting_exports_for_report with no expenses in database
    Case: Non-existent report_id
    """
    workspace = Workspace.objects.get(id=1)
    report_id = 'rpNonExistent123'

    _delete_accounting_exports_for_report(report_id, workspace)


def test_delete_accounting_exports_for_report_with_active_exports(db, mocker, add_expense_report_data):
    """
    Test _delete_accounting_exports_for_report skips exports with active status
    """
    workspace = Workspace.objects.get(id=1)
    accounting_export = add_expense_report_data['accounting_export']

    accounting_export.status = 'IN_PROGRESS'
    accounting_export.save()

    report_id = accounting_export.expenses.first().report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    _delete_accounting_exports_for_report(report_id, workspace)

    assert not mock_delete.called


def test_delete_accounting_exports_for_report_preserves_exported(db, mocker, add_expense_report_data):
    """
    Test _delete_accounting_exports_for_report preserves exported accounting exports
    """
    workspace = Workspace.objects.get(id=1)

    accounting_export = add_expense_report_data['accounting_export']

    accounting_export.exported_at = datetime.now(tz=timezone.utc)
    accounting_export.save()

    report_id = accounting_export.expenses.first().report_id

    mock_delete = mocker.patch('apps.fyle.tasks.delete_accounting_export_and_related_data')

    _delete_accounting_exports_for_report(report_id, workspace)

    assert not mock_delete.called


def test_handle_expense_ejected_from_report_removes_from_export(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report removes expense from export
    """
    workspace = Workspace.objects.get(id=1)

    accounting_export = add_expense_report_data['accounting_export']
    expenses = add_expense_report_data['expenses']

    expense_to_remove = expenses[0]

    expense_data = {
        'id': expense_to_remove.expense_id,
        'report_id': None
    }

    initial_expense_count = accounting_export.expenses.count()

    _handle_expense_ejected_from_report(expense_to_remove, expense_data, workspace)

    accounting_export.refresh_from_db()

    assert accounting_export.expenses.count() == initial_expense_count - 1
    assert expense_to_remove not in accounting_export.expenses.all()
    assert AccountingExport.objects.filter(id=accounting_export.id).exists()


def test_handle_expense_ejected_from_report_deletes_empty_export(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report deletes export when last expense is removed
    """
    workspace = Workspace.objects.get(id=1)

    accounting_export = add_expense_report_data['accounting_export']
    expense = add_expense_report_data['expenses'][0]
    accounting_export.expenses.set([expense])

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    export_id = accounting_export.id

    _handle_expense_ejected_from_report(expense, expense_data, workspace)

    assert not AccountingExport.objects.filter(id=export_id).exists()


def test_handle_expense_ejected_from_report_no_export_found(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report when expense has no export
    """
    workspace = Workspace.objects.get(id=1)
    expense = add_expense_report_data['expenses'][0]

    # Remove expense from its export to simulate orphaned expense
    accounting_export = add_expense_report_data['accounting_export']
    accounting_export.expenses.remove(expense)

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    _handle_expense_ejected_from_report(expense, expense_data, workspace)


def test_handle_expense_ejected_from_report_with_active_export(db, add_expense_report_data):
    """
    Test _handle_expense_ejected_from_report skips removal when export status is active
    """
    workspace = Workspace.objects.get(id=1)

    accounting_export = add_expense_report_data['accounting_export']
    expense = add_expense_report_data['expenses'][0]
    initial_count = accounting_export.expenses.count()

    accounting_export.status = 'ENQUEUED'
    accounting_export.save()

    expense_data = {
        'id': expense.expense_id,
        'report_id': None
    }

    _handle_expense_ejected_from_report(expense, expense_data, workspace)

    accounting_export.refresh_from_db()

    assert accounting_export.expenses.count() == initial_count
    assert expense in accounting_export.expenses.all()


def test_handle_expense_report_change_ejected_expense_not_found(db, mocker, create_temp_workspace):
    """
    Test handle_expense_report_change when expense doesn't exist in workspace (EJECTED_FROM_REPORT)
    """
    workspace = Workspace.objects.get(id=1)

    expense_data = {
        'id': 'txNonExistent999',
        'org_id': workspace.org_id,
        'report_id': None
    }

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')


def test_handle_expense_report_change_ejected_from_exported_export(db, add_expense_report_data):
    """
    Test handle_expense_report_change skips when expense is part of exported export (EJECTED_FROM_REPORT)
    """
    workspace = Workspace.objects.get(id=1)
    accounting_export = add_expense_report_data['accounting_export']
    expense = add_expense_report_data['expenses'][0]

    accounting_export.exported_at = datetime.now(tz=timezone.utc)
    accounting_export.save()

    expense_data = {
        'id': expense.expense_id,
        'org_id': workspace.org_id,
        'report_id': None
    }

    handle_expense_report_change(expense_data, 'EJECTED_FROM_REPORT')

    accounting_export.refresh_from_db()
    assert expense in accounting_export.expenses.all()


def test_handle_category_changes_for_expense_removes_old_error(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker,
    create_category_expense_attribute,
    create_category_mapping_error
):
    """
    Test handle_category_changes_for_expense removes expense from old category mapping error
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    old_category_attribute = create_category_expense_attribute('Old Category')
    error = create_category_mapping_error(old_category_attribute, mapping_error_accounting_export_ids=[accounting_export.id, 999])

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='New Category')

    error.refresh_from_db()
    assert accounting_export.id not in error.mapping_error_accounting_export_ids
    assert 999 in error.mapping_error_accounting_export_ids


def test_handle_category_changes_for_expense_deletes_empty_error(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker,
    create_category_expense_attribute,
    create_category_mapping_error
):
    """
    Test handle_category_changes_for_expense deletes error when no accounting exports remain
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    old_category_attribute = create_category_expense_attribute('Old Category')
    error = create_category_mapping_error(old_category_attribute, mapping_error_accounting_export_ids=[accounting_export.id])
    error_id = error.id

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='New Category')

    assert not Error.objects.filter(id=error_id).exists()


def test_handle_category_changes_for_expense_creates_new_error(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker,
    create_category_expense_attribute
):
    """
    Test handle_category_changes_for_expense creates error for unmapped new category
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    new_category_attribute = create_category_expense_attribute('Unmapped Category')

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='Unmapped Category')

    new_error = Error.objects.filter(
        workspace_id=workspace_id,
        type='CATEGORY_MAPPING',
        expense_attribute=new_category_attribute
    ).first()
    assert new_error is not None
    assert accounting_export.id in new_error.mapping_error_accounting_export_ids
    assert new_error.error_title == 'Unmapped Category'


def test_handle_category_changes_for_expense_adds_to_existing_error(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker,
    create_category_expense_attribute,
    create_category_mapping_error
):
    """
    Test handle_category_changes_for_expense adds to existing error for new category
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    new_category_attribute = create_category_expense_attribute('Category With Error')
    existing_error = create_category_mapping_error(new_category_attribute, mapping_error_accounting_export_ids=[888])

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='Category With Error')

    existing_error.refresh_from_db()
    assert accounting_export.id in existing_error.mapping_error_accounting_export_ids
    assert 888 in existing_error.mapping_error_accounting_export_ids


def test_handle_category_changes_for_expense_no_accounting_export(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test handle_category_changes_for_expense returns early when no accounting_export exists
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='New Category')


def test_handle_category_changes_for_expense_no_old_category_error(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker,
    create_category_expense_attribute
):
    """
    Test handle_category_changes_for_expense handles case when old category has no error
    """
    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    create_category_expense_attribute('Old Category')

    handle_category_changes_for_expense(expense=expense, old_category='Old Category', new_category='New Category')


def test_update_non_exported_expenses_with_category_change(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test update_non_exported_expenses detects and handles category change
    """
    workspace_id = 1

    original_expense_data = data['category_change_expense']
    org_id = original_expense_data['org_id']

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_id = org_id
    workspace.save()

    expense_created, _ = Expense.objects.update_or_create(
        org_id=org_id,
        expense_id=original_expense_data['id'],
        workspace_id=workspace_id,
        defaults={
            'fund_source': original_expense_data['fund_source'],
            'category': original_expense_data['category'],
            'sub_category': original_expense_data['sub_category'],
            'amount': original_expense_data['amount'],
            'currency': original_expense_data['currency'],
            'employee_email': original_expense_data['employee_email'],
            'report_id': original_expense_data['report_id']
        }
    )

    # Create an accounting export for this expense
    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source=original_expense_data['fund_source'],
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense_created)

    mock_handle_category_changes = mocker.patch('apps.fyle.tasks.handle_category_changes_for_expense')

    updated_expense_data = data['updated_category_expense']
    mock_fyle_expenses = mocker.patch('apps.fyle.tasks.FyleExpenses.construct_expense_object')
    mock_fyle_expenses.return_value = [{
        'source_account_type': updated_expense_data['source_account_type'],
        'category': updated_expense_data['category'],
        'sub_category': updated_expense_data['sub_category']
    }]

    mocker.patch('apps.fyle.tasks.Expense.create_expense_objects')

    update_non_exported_expenses(updated_expense_data)

    mock_handle_category_changes.assert_called_once()
    call_kwargs = mock_handle_category_changes.call_args[1]
    assert call_kwargs['new_category'] == 'New Category'


def test_update_non_exported_expenses_no_category_change(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test update_non_exported_expenses does not call handler when category unchanged
    """
    workspace_id = 1

    original_expense_data = data['category_change_expense']
    org_id = original_expense_data['org_id']

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_id = org_id
    workspace.save()

    expense_created, _ = Expense.objects.update_or_create(
        org_id=org_id,
        expense_id=original_expense_data['id'],
        workspace_id=workspace_id,
        defaults={
            'fund_source': original_expense_data['fund_source'],
            'category': original_expense_data['category'],
            'sub_category': original_expense_data['sub_category'],
            'amount': original_expense_data['amount'],
            'currency': original_expense_data['currency'],
            'employee_email': original_expense_data['employee_email'],
            'report_id': original_expense_data['report_id']
        }
    )

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source=original_expense_data['fund_source'],
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense_created)

    mock_handle_category_changes = mocker.patch('apps.fyle.tasks.handle_category_changes_for_expense')

    mock_fyle_expenses = mocker.patch('apps.fyle.tasks.FyleExpenses.construct_expense_object')
    mock_fyle_expenses.return_value = [{
        'source_account_type': original_expense_data['source_account_type'],
        'category': original_expense_data['category'],
        'sub_category': original_expense_data['sub_category']
    }]

    mocker.patch('apps.fyle.tasks.Expense.create_expense_objects')

    update_non_exported_expenses(original_expense_data)

    mock_handle_category_changes.assert_not_called()


def test_validate_failing_export_mapping_errors_returns_true(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test validate_failing_export returns (True, True) when mapping error exists
    """
    from fyle_accounting_mappings.models import ExpenseAttribute

    from apps.sage300.exports.helpers import validate_failing_export

    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    category_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        value='Test Category',
        display_name='Test Category',
        active=True
    )

    Error.objects.create(
        workspace_id=workspace_id,
        type='CATEGORY_MAPPING',
        expense_attribute=category_attribute,
        mapping_error_accounting_export_ids=[accounting_export.id],
        error_title='Test Category',
        error_detail='Category mapping is missing',
        is_resolved=False
    )

    skip_export, is_mapping_error = validate_failing_export(
        is_auto_export=False,
        interval_hours=0,
        error=None,
        accounting_export=accounting_export
    )

    assert skip_export is True
    assert is_mapping_error is True


def test_validate_failing_export_mapping_errors_returns_false(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test validate_failing_export returns (False, False) when no mapping error exists
    """
    from apps.sage300.exports.helpers import validate_failing_export

    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    skip_export, is_mapping_error = validate_failing_export(
        is_auto_export=False,
        interval_hours=0,
        error=None,
        accounting_export=accounting_export
    )

    assert skip_export is False
    assert is_mapping_error is False


def test_validate_failing_export_mapping_errors_ignores_resolved(
    db,
    create_temp_workspace,
    add_export_settings,
    mocker
):
    """
    Test validate_failing_export ignores resolved mapping errors
    """
    from fyle_accounting_mappings.models import ExpenseAttribute

    from apps.sage300.exports.helpers import validate_failing_export

    workspace_id = 1

    category_expense_data = data['category_change_expense']
    expense_objects = Expense.create_expense_objects([category_expense_data], workspace_id)
    expense = expense_objects[0]

    accounting_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='EXPORT_READY',
        description={'test': 'data'}
    )
    accounting_export.expenses.add(expense)

    category_attribute = ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        value='Test Category',
        display_name='Test Category',
        active=True
    )

    Error.objects.create(
        workspace_id=workspace_id,
        type='CATEGORY_MAPPING',
        expense_attribute=category_attribute,
        mapping_error_accounting_export_ids=[accounting_export.id],
        error_title='Test Category',
        error_detail='Category mapping is missing',
        is_resolved=True
    )

    skip_export, is_mapping_error = validate_failing_export(
        is_auto_export=False,
        interval_hours=0,
        error=None,
        accounting_export=accounting_export
    )

    assert skip_export is False
    assert is_mapping_error is False


def test_handle_org_setting_updated(db, create_temp_workspace):
    """
    Test handle_org_setting_updated stores regional_settings in org_settings field
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)

    workspace.org_settings = {}
    workspace.save()

    handle_org_setting_updated(
        workspace_id=workspace_id,
        org_settings=fyle_fixtures['org_settings']['org_settings_payload']
    )

    workspace.refresh_from_db()

    assert workspace.org_settings == fyle_fixtures['org_settings']['expected_org_settings']
    assert 'other_setting' not in workspace.org_settings


def test_handle_org_setting_updated_empty_regional_settings(db, create_temp_workspace):
    """
    Test handle_org_setting_updated when regional_settings is empty or missing
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)

    handle_org_setting_updated(
        workspace_id=workspace_id,
        org_settings=fyle_fixtures['org_settings']['org_settings_payload_without_regional']
    )

    workspace.refresh_from_db()
    assert workspace.org_settings == fyle_fixtures['org_settings']['expected_org_settings_empty']


def test_handle_org_setting_updated_overwrites_existing(db, create_temp_workspace):
    """
    Test handle_org_setting_updated overwrites existing org_settings
    """
    workspace_id = 1
    workspace = Workspace.objects.get(id=workspace_id)

    workspace.org_settings = fyle_fixtures['org_settings']['expected_org_settings']
    workspace.save()

    handle_org_setting_updated(
        workspace_id=workspace_id,
        org_settings=fyle_fixtures['org_settings']['org_settings_payload_updated']
    )

    workspace.refresh_from_db()
    assert workspace.org_settings == fyle_fixtures['org_settings']['expected_org_settings_updated']
