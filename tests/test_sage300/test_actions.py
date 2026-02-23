import pytest

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.sage300.actions import update_accounting_export_summary


@pytest.mark.django_db
def test_update_accounting_export_summary(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_accounting_export_summary
):
    """Test update_accounting_export_summary updates counts correctly"""
    workspace_id = 1

    # Clear last_exported_at so all COMPLETE exports are counted
    AccountingExportSummary.objects.filter(workspace_id=workspace_id).update(last_exported_at=None)

    AccountingExport.objects.filter(
        workspace_id=workspace_id, type='PURCHASE_INVOICE'
    ).update(status='FAILED')

    AccountingExport.objects.filter(
        workspace_id=workspace_id, type='DIRECT_COST'
    ).update(status='COMPLETE')

    result = update_accounting_export_summary(workspace_id)

    assert result.failed_accounting_export_count == 1
    assert result.successful_accounting_export_count == 1
    assert result.total_accounting_export_count == 2


@pytest.mark.django_db
def test_update_accounting_export_summary_excludes_fetch_types(
    db,
    create_temp_workspace,
    add_accounting_export_expenses,
    add_accounting_export_summary
):
    """Test that FETCHING_* types are excluded from counts"""
    workspace_id = 1

    AccountingExport.objects.filter(
        workspace_id=workspace_id
    ).exclude(
        type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']
    ).delete()

    AccountingExport.objects.filter(
        workspace_id=workspace_id, type__startswith='FETCHING'
    ).update(status='FAILED')

    result = update_accounting_export_summary(workspace_id)

    assert result.failed_accounting_export_count == 0
    assert result.total_accounting_export_count == 0


@pytest.mark.django_db
def test_update_accounting_export_summary_not_found(
    db,
    create_temp_workspace
):
    """Test update_accounting_export_summary raises when summary doesn't exist"""
    with pytest.raises(AccountingExportSummary.DoesNotExist):
        update_accounting_export_summary(workspace_id=1)
