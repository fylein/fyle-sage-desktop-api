import pytest
from unittest.mock import patch

from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.helpers import clear_workspace_errors_on_export_type_change
from apps.workspaces.models import ExportSetting


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

    personal_export = AccountingExport.objects.filter(fund_source='PERSONAL').first()
    ccc_export = AccountingExport.objects.filter(fund_source='CCC').first()
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
