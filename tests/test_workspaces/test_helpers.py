import pytest
from unittest.mock import patch

from tests.test_fyle.fixtures import fixtures as fyle_fixtures
from apps.accounting_exports.models import AccountingExport, Error
from apps.fyle.models import Expense
from apps.workspaces.helpers import (
    clear_workspace_errors_on_export_type_change,
    get_fund_source,
    get_grouping_types,
    get_source_account_type,
    construct_filter_for_affected_accounting_exports
)
from apps.workspaces.models import ExportSetting
from apps.workspaces.signals import run_post_save_export_settings_triggers


def test_clear_workspace_errors_no_changes(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_errors,
    add_export_settings
):
    workspace_id = 1

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': None
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    initial_error_count = Error.objects.filter(workspace_id=workspace_id).count()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    assert Error.objects.filter(workspace_id=workspace_id).count() == initial_error_count

    personal_export = AccountingExport.objects.filter(workspace_id=workspace_id, fund_source='PERSONAL').first()
    ccc_export = AccountingExport.objects.filter(workspace_id=workspace_id, fund_source='CCC').first()
    assert personal_export.status == 'EXPORT_QUEUED'
    assert ccc_export.status == 'EXPORT_QUEUED'


def test_clear_workspace_errors_reimbursable_change(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_errors,
    add_export_settings
):
    workspace_id = 1

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': None
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_export_type = None
    export_setting.save()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    mapping_errors = Error.objects.filter(
        workspace_id=workspace_id,
        type__in=['EMPLOYEE_MAPPING', 'CATEGORY_MAPPING'],
        is_resolved=False
    )
    assert mapping_errors.count() == 0

    personal_exports = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        fund_source='PERSONAL',
        exported_at__isnull=True,
        status='EXPORT_READY'
    )
    assert personal_exports.exists()


def test_clear_workspace_errors_ccc_change(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_errors,
    add_export_settings
):
    workspace_id = 1

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE'
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.credit_card_expense_export_type = None
    export_setting.save()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    mapping_errors = Error.objects.filter(
        workspace_id=workspace_id,
        type__in=['EMPLOYEE_MAPPING', 'CATEGORY_MAPPING'],
        is_resolved=False
    )
    assert mapping_errors.count() == 0

    ccc_exports = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        fund_source='CCC',
        exported_at__isnull=True,
        status='EXPORT_READY'
    )
    assert ccc_exports.exists()


def test_clear_workspace_errors_only_unresolved_deleted(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_export_settings
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(workspace_id=workspace_id).first()

    resolved_error = Error.objects.create(
        workspace_id=workspace_id,
        type='EMPLOYEE_MAPPING',
        accounting_export=accounting_export,
        error_title='Resolved Mapping Error',
        error_detail='Employee mapping missing',
        is_resolved=True
    )

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE'
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_export_type = None
    export_setting.save()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    assert Error.objects.filter(id=resolved_error.id).exists()

    unresolved_errors = Error.objects.filter(
        workspace_id=workspace_id,
        type__in=['EMPLOYEE_MAPPING', 'CATEGORY_MAPPING'],
        is_resolved=False
    )
    assert unresolved_errors.count() == 0


def test_clear_workspace_errors_exception_handling(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_errors
):
    workspace_id = 1

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE'
    }

    invalid_export_setting = None

    with pytest.raises(AttributeError):
        clear_workspace_errors_on_export_type_change(
            workspace_id=workspace_id,
            old_export_settings=old_export_settings,
            new_export_settings=invalid_export_setting
        )


def test_clear_workspace_errors_exported_accounting_exports_unchanged(
    db,
    create_temp_workspace,
    add_export_settings
):
    workspace_id = 1

    exported_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='FAILED',
        exported_at='2024-01-01T00:00:00Z'
    )

    unexported_export = AccountingExport.objects.create(
        workspace_id=workspace_id,
        type='PURCHASE_INVOICE',
        fund_source='PERSONAL',
        status='FAILED',
        exported_at=None
    )

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE'
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_export_type = None
    export_setting.save()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    exported_export.refresh_from_db()
    assert exported_export.status == 'FAILED'
    assert exported_export.exported_at is not None

    unexported_export.refresh_from_db()
    assert unexported_export.status == 'EXPORT_READY'


def test_clear_workspace_errors_with_accounting_export_errors(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_export_settings
):
    workspace_id = 1
    accounting_export = AccountingExport.objects.filter(
        workspace_id=workspace_id,
        fund_source='PERSONAL',
        exported_at__isnull=True
    ).first()

    Error.objects.create(
        workspace_id=workspace_id,
        type='SAGE300_ERROR',
        accounting_export=accounting_export,
        error_title='Accounting Export Error',
        error_detail='Export failed',
        is_resolved=False
    )

    old_export_settings = {
        'reimbursable_expenses_export_type': 'PURCHASE_INVOICE',
        'credit_card_expense_export_type': 'PURCHASE_INVOICE'
    }

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_export_type = None
    export_setting.save()

    clear_workspace_errors_on_export_type_change(
        workspace_id=workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=export_setting
    )

    accounting_export_errors = Error.objects.filter(
        workspace_id=workspace_id,
        accounting_export=accounting_export
    )
    assert accounting_export_errors.count() == 0


@patch('apps.workspaces.signals.clear_workspace_errors_on_export_type_change')
@patch('apps.workspaces.signals.update_accounting_export_summary')
def test_export_settings_signal_with_last_exported_at(
    mock_update_summary,
    mock_clear_errors,
    db,
    simple_export_settings,
    simple_accounting_export_summary
):
    workspace_id = 1

    simple_export_settings.reimbursable_expenses_export_type = None
    simple_export_settings.save()

    mock_clear_errors.assert_called_once()
    mock_update_summary.assert_called_once_with(workspace_id)


@patch('apps.workspaces.signals.update_accounting_export_summary')
@patch('apps.workspaces.signals.clear_workspace_errors_on_export_type_change')
def test_export_settings_signal_fallback_case(
    mock_clear_errors,
    mock_update_summary,
    db,
    create_temp_workspace
):
    """
    Test post_save signal fallback case when _pre_save_old_export_settings is not available
    """
    workspace_id = 1

    export_setting = ExportSetting(
        workspace_id=workspace_id,
        reimbursable_expenses_export_type='PURCHASE_INVOICE',
        credit_card_expense_export_type=None
    )

    run_post_save_export_settings_triggers(
        sender=ExportSetting,
        instance=export_setting,
        created=True
    )

    expected_old_settings = {
        'reimbursable_expenses_export_type': None,
        'credit_card_expense_export_type': None,
    }

    mock_clear_errors.assert_called_once_with(
        workspace_id=workspace_id,
        old_export_settings=expected_old_settings,
        new_export_settings=export_setting
    )


def test_get_fund_source(db, create_temp_workspace, add_export_settings):
    """
    Test get_fund_source helper function
    """

    workspace_id = 1

    # Test with only reimbursable enabled (default fixture behavior)
    fund_sources = get_fund_source(workspace_id)
    assert fund_sources == ['PERSONAL']

    # Test with both reimbursable and credit card enabled
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.save()

    fund_sources = get_fund_source(workspace_id)
    expected_sources = ['PERSONAL', 'CCC']
    assert set(fund_sources) == set(expected_sources)

    # Test with only credit card enabled
    export_setting.reimbursable_expenses_export_type = None
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.save()

    fund_sources = get_fund_source(workspace_id)
    assert fund_sources == ['CCC']

    # Test with neither enabled
    export_setting.credit_card_expense_export_type = None
    export_setting.save()

    fund_sources = get_fund_source(workspace_id)
    assert fund_sources == []


def test_get_grouping_types(db, create_temp_workspace, add_export_settings):
    """
    Test get_grouping_types helper function
    """

    workspace_id = 1

    # Test default grouping (fixture has REPORT grouping)
    grouping_types = get_grouping_types(workspace_id)
    expected_types = {'PERSONAL': 'report', 'CCC': 'report'}
    assert grouping_types == expected_types

    # Test with expense grouping enabled
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expense_grouped_by = 'EXPENSE'
    export_setting.credit_card_expense_grouped_by = 'EXPENSE'
    export_setting.save()

    grouping_types = get_grouping_types(workspace_id)
    expected_types = {'PERSONAL': 'expense', 'CCC': 'expense'}
    assert grouping_types == expected_types

    # Test with mixed grouping
    export_setting.reimbursable_expense_grouped_by = 'EXPENSE'
    export_setting.credit_card_expense_grouped_by = 'REPORT'
    export_setting.save()

    grouping_types = get_grouping_types(workspace_id)
    expected_types = {'PERSONAL': 'expense', 'CCC': 'report'}
    assert grouping_types == expected_types


def test_get_source_account_type():
    """
    Test get_source_account_type helper function
    """

    # Test with PERSONAL fund source
    source_account_types = get_source_account_type(['PERSONAL'])
    assert source_account_types == ['PERSONAL_CASH_ACCOUNT']

    # Test with CCC fund source
    source_account_types = get_source_account_type(['CCC'])
    assert source_account_types == ['PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT']

    # Test with both fund sources
    source_account_types = get_source_account_type(['PERSONAL', 'CCC'])
    expected_types = ['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT']
    assert set(source_account_types) == set(expected_types)

    # Test with empty list
    source_account_types = get_source_account_type([])
    assert source_account_types == []


def test_construct_filter_for_affected_accounting_exports(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses
):
    """
    Test construct_filter_for_affected_accounting_exports helper function
    """
    workspace_id = 1
    report_id = 'rpFundTest123'

    # Create test expenses with fund source change data
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']

    # Create expense objects
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]

    # Create accounting exports
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

    # Test with expense grouping
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_grouped_by = 'expense'
    export_setting.credit_card_expenses_grouped_by = 'expense'
    export_setting.save()

    affected_fund_source_expense_ids = {
        'PERSONAL': [expense_ids[0]],
        'CCC': [expense_ids[1]]
    }

    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Apply filter and verify results
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()

    # Test with report grouping
    export_setting.reimbursable_expenses_grouped_by = 'report'
    export_setting.credit_card_expenses_grouped_by = 'report'
    export_setting.save()

    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Apply filter and verify results
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()

    # Test with mixed grouping
    export_setting.reimbursable_expenses_grouped_by = 'expense'
    export_setting.credit_card_expenses_grouped_by = 'report'
    export_setting.save()

    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    # Apply filter and verify results
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()

    # Test with no affected fund source expenses but still have changed expense IDs
    empty_affected_fund_source_expense_ids = {'PERSONAL': [], 'CCC': []}
    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=empty_affected_fund_source_expense_ids
    )

    # Should still find exports because we have changed_expense_ids
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()


def test_get_fund_source_export_setting_not_found(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test get_fund_source when ExportSetting does not exist
    """
    workspace_id = 999  # Non-existent workspace
    
    # Mock logger
    mock_logger = mocker.patch('apps.workspaces.helpers.logger')
    
    # Call the function
    fund_sources = get_fund_source(workspace_id)
    
    # Should return empty list and log warning
    assert fund_sources == []
    mock_logger.warning.assert_called_with(
        "ExportSetting not found for workspace %s, returning empty fund sources", 
        workspace_id
    )


def test_get_grouping_types_export_setting_not_found(
    db,
    create_temp_workspace,
    mocker
):
    """
    Test get_grouping_types when ExportSetting does not exist
    """
    workspace_id = 999  # Non-existent workspace
    
    # Mock logger
    mock_logger = mocker.patch('apps.workspaces.helpers.logger')
    
    # Call the function
    grouping_types = get_grouping_types(workspace_id)
    
    # Should return empty dict and log warning
    assert grouping_types == {}
    mock_logger.warning.assert_called_with("ExportSetting not found for workspace %s", workspace_id)


def test_construct_filter_mixed_grouping_personal_report_ccc_expense(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses
):
    """
    Test construct_filter_for_affected_accounting_exports with mixed grouping: PERSONAL=report, CCC=expense
    """
    workspace_id = 1
    report_id = 'rpFundTest123'
    
    # Set mixed grouping: PERSONAL=report, CCC=expense
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_grouped_by = 'report'
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.credit_card_expenses_grouped_by = 'expense'
    export_setting.save()
    
    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]
    
    # Create accounting exports
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
    
    affected_fund_source_expense_ids = {
        'PERSONAL': [expense_ids[0]],
        'CCC': [expense_ids[1]]
    }
    
    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )
    
    # Apply filter and verify results
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()


def test_construct_filter_mixed_grouping_personal_expense_ccc_report(
    db,
    create_temp_workspace,
    add_export_settings,
    add_accounting_export_expenses
):
    """
    Test construct_filter_for_affected_accounting_exports with mixed grouping: PERSONAL=expense, CCC=report
    """
    workspace_id = 1
    report_id = 'rpFundTest123'
    
    # Set mixed grouping: PERSONAL=expense, CCC=report
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)
    export_setting.reimbursable_expenses_grouped_by = 'expense'
    export_setting.credit_card_expense_export_type = 'PURCHASE_INVOICE'
    export_setting.credit_card_expenses_grouped_by = 'report'
    export_setting.save()
    
    # Create test expenses
    fund_source_expenses = fyle_fixtures['fund_source_change_expenses']
    expense_objects = Expense.create_expense_objects(fund_source_expenses, workspace_id)
    expense_ids = [expense.id for expense in expense_objects]
    
    # Create accounting exports
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
    
    affected_fund_source_expense_ids = {
        'PERSONAL': [expense_ids[0]],
        'CCC': [expense_ids[1]]
    }
    
    filter_query = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        changed_expense_ids=expense_ids,
        report_id=report_id,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )
    
    # Apply filter and verify results
    affected_exports = AccountingExport.objects.filter(filter_query, workspace_id=workspace_id)
    assert affected_exports.exists()
