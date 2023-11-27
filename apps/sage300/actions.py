from django.db.models import Q

from apps.workspaces.models import LastExportDetail
from apps.accounting_exports.models import AccountingExport


def update_last_export_details(workspace_id):
    last_export_detail = LastExportDetail.objects.get(workspace_id=workspace_id)

    failed_exports = AccountingExport.objects.filter(~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']).count()

    successful_exports = AccountingExport.objects.filter(
        ~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']),
        workspace_id=workspace_id, status='COMPLETE',
    ).count()

    last_export_detail.failed_expense_groups_count = failed_exports
    last_export_detail.successful_expense_groups_count = successful_exports
    last_export_detail.total_expense_groups_count = failed_exports + successful_exports
    last_export_detail.save()

    return last_export_detail
