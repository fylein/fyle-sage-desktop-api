from django.db.models import Q
from datetime import datetime, timezone

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.workspaces.models import Workspace, Sage300Credential, ExportSetting
from apps.sage300.utils import SageDesktopConnector
from workers.helpers import RoutingKeyEnum, WorkerActionEnum, publish_to_rabbitmq


def get_sage_connector(workspace_id):
    """
    Get Sage Desktop Connector
    :param workspace_id: Workspace id
    :return: SageDesktopConnector
    """
    sage_credentials = Sage300Credential.get_active_sage300_credentials(
        workspace_id=workspace_id
    )
    return SageDesktopConnector(credentials_object=sage_credentials, workspace_id=workspace_id)


def sync_dimensions(workspace_id):
    """
    Sync dimensions from Sage 300
    :param workspace_id: Workspace id
    :return: None
    """
    workspace = Workspace.objects.get(id=workspace_id)
    if workspace.destination_synced_at:
        time_interval = datetime.now(timezone.utc) - workspace.destination_synced_at

    if workspace.destination_synced_at is None or time_interval.days > 0:
        sage_connector = get_sage_connector(workspace_id=workspace_id)

        # Sync dimensions
        sage_connector.sync_accounts()
        sage_connector.sync_vendors()
        sage_connector.sync_jobs()
        sage_connector.sync_commitments()
        sage_connector.sync_standard_categories()
        sage_connector.sync_standard_cost_codes()

        workspace.destination_synced_at = datetime.now()
        workspace.save(update_fields=["destination_synced_at"])


def refresh_sage_dimension(workspace_id):
    """
    Refresh Sage 300 dimensions and trigger import to Fyle
    :param workspace_id: Workspace id
    :return: None
    """
    get_sage_connector(workspace_id=workspace_id)
    export_settings = ExportSetting.objects.filter(workspace_id=workspace_id).first()

    if export_settings:
        payload = {
            'workspace_id': workspace_id,
            'action': WorkerActionEnum.IMPORT_DIMENSIONS_TO_FYLE.value,
            'data': {
                'workspace_id': workspace_id
            }
        }
        publish_to_rabbitmq(payload=payload, routing_key=RoutingKeyEnum.IMPORT.value)


def update_accounting_export_summary(workspace_id):
    accounting_export_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)

    failed_exports = AccountingExport.objects.filter(~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']), workspace_id=workspace_id, status__in=['FAILED', 'FATAL']).count()
    filters = {
        'workspace_id': workspace_id,
        'status': 'COMPLETE'
    }

    if accounting_export_summary.last_exported_at:
        filters['updated_at__gte'] = accounting_export_summary.last_exported_at

    successful_exports = AccountingExport.objects.filter(
        ~Q(type__in=['FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_CREDIT_CARD_EXPENSES']),
        **filters
    ).count()

    accounting_export_summary.failed_accounting_export_count = failed_exports
    accounting_export_summary.successful_accounting_export_count = successful_exports
    accounting_export_summary.total_accounting_export_count = failed_exports + successful_exports
    accounting_export_summary.save()

    return accounting_export_summary
