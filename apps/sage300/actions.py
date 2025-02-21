from django.db.models import Q

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary


def update_accounting_export_summary(workspace_id):
    accounting_export_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    print(accounting_export_summary.__dict__)

    failed_exports = AccountingExport.objects.filter(~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']).count()
    filters = {
        'workspace_id': workspace_id,
        'status': 'COMPLETE'
    }
    print(filters, "1")

    if accounting_export_summary:
        filters['updated_at__gte'] = accounting_export_summary.last_exported_at

    print(filters, "2")

    successful_exports = AccountingExport.objects.filter(
        ~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']),
        **filters
    ).count()

    print(successful_exports.__dict__, "3")

    accounting_export_summary.failed_accounting_export_count = failed_exports
    accounting_export_summary.successful_accounting_export_count = successful_exports
    accounting_export_summary.total_accounting_export_count = failed_exports + successful_exports
    accounting_export_summary.save()

    return accounting_export_summary
