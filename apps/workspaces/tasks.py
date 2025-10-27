import logging
from datetime import datetime, timedelta
from typing import List

from django.conf import settings
from django.db.models import Q
from django_q.models import Schedule
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_integrations_platform_connector import PlatformConnector

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary
from apps.fyle.helpers import patch_request
from apps.fyle.queue import queue_import_credit_card_expenses, queue_import_reimbursable_expenses
from apps.sage300.exports.direct_cost.tasks import ExportDirectCost
from apps.sage300.exports.purchase_invoice.tasks import ExportPurchaseInvoice
from apps.workspaces.models import AdvancedSetting, ExportSetting, FyleCredential

logger = logging.getLogger(__name__)


def async_update_fyle_credentials(fyle_org_id: str, refresh_token: str):
    fyle_credentials = FyleCredential.objects.filter(workspace__org_id=fyle_org_id).first()
    if fyle_credentials and refresh_token:
        fyle_credentials.refresh_token = refresh_token
        fyle_credentials.save()


def run_import_export(workspace_id: int, export_mode = None):
    """
    Run process to export to sage300

    :param workspace_id: Workspace id
    """

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    accounting_summary = AccountingExportSummary.objects.filter(workspace_id=workspace_id).first()

    interval_hours = advance_settings.interval_hours
    is_auto_export = advance_settings.schedule_is_enabled

    last_exported_at = datetime.now()
    is_expenses_exported = False

    export_map = {
        'PURCHASE_INVOICE': ExportPurchaseInvoice(),
        'DIRECT_COST': ExportDirectCost()
    }

    # For Reimbursable Expenses
    if export_settings.reimbursable_expenses_export_type:
        queue_import_reimbursable_expenses(workspace_id=workspace_id,  synchronous=True, imported_from=ExpenseImportSourceEnum.BACKGROUND_SCHEDULE)
        accounting_export = AccountingExport.objects.get(
            workspace_id=workspace_id,
            type='FETCHING_REIMBURSABLE_EXPENSES'
        )

        if accounting_export.status == 'COMPLETE':
            accounting_export_ids = AccountingExport.objects.filter(
                Q(status='EXPORT_READY') | Q(type__in=['PURCHASE_INVOICE', 'DIRECT_COST']),
                fund_source='PERSONAL',
                exported_at__isnull=True,
                workspace_id=workspace_id
            ).exclude(
                status='FAILED',
                re_attempt_export=False
            ).values_list('id', flat=True).distinct()

            if len(accounting_export_ids):
                is_expenses_exported = True
                export = export_map[export_settings.reimbursable_expenses_export_type]
                export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours, triggered_by=ExpenseImportSourceEnum.BACKGROUND_SCHEDULE)

    # For Credit Card Expenses
    if export_settings.credit_card_expense_export_type:
        queue_import_credit_card_expenses(workspace_id=workspace_id, synchronous=True, imported_from=ExpenseImportSourceEnum.BACKGROUND_SCHEDULE)
        accounting_export = AccountingExport.objects.get(
            workspace_id=workspace_id,
            type='FETCHING_CREDIT_CARD_EXPENSES'
        )
        if accounting_export.status == 'COMPLETE':
            accounting_export_ids = AccountingExport.objects.filter(
                Q(status='EXPORT_READY') | Q(type__in=['PURCHASE_INVOICE', 'DIRECT_COST']),
                fund_source='CCC',
                exported_at__isnull=True,
                workspace_id=workspace_id
            ).exclude(
                status='FAILED',
                re_attempt_export=False
            ).values_list('id', flat=True).distinct()

            if len(accounting_export_ids):
                is_expenses_exported = True
                export = export_map[export_settings.credit_card_expense_export_type]
                export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours, triggered_by=ExpenseImportSourceEnum.BACKGROUND_SCHEDULE)

    if is_expenses_exported:
        accounting_summary.last_exported_at = last_exported_at
        accounting_summary.export_mode = export_mode or 'MANUAL'

        if advance_settings and advance_settings.schedule_is_enabled:
            accounting_summary.next_export_at = last_exported_at + timedelta(hours=advance_settings.interval_hours)

        accounting_summary.save()


def schedule_sync(workspace_id: int, schedule_enabled: bool, hours: int, email_added: List, emails_selected: List):
    """
    Configure sync schedule settings for a workspace
    """
    advance_settings = AdvancedSetting.objects.get(workspace_id=workspace_id)
    advance_settings.schedule_is_enabled = schedule_enabled

    if schedule_enabled:
        _enable_schedule(advance_settings, hours, email_added, emails_selected)
    else:
        _disable_schedule(advance_settings)

    return advance_settings


def _enable_schedule(advance_settings, hours: int, email_added: List, emails_selected: List):
    """
    Enable sync schedule and configure settings
    """
    advance_settings.start_datetime = datetime.now()
    advance_settings.interval_hours = hours
    advance_settings.emails_selected = emails_selected

    if email_added:
        advance_settings.emails_added = email_added

    if advance_settings.is_real_time_export_enabled:
        _cleanup_existing_schedule(advance_settings)
    else:
        _create_or_update_schedule(advance_settings, hours)


def _disable_schedule(advance_settings):
    """
    Disable sync schedule and cleanup existing schedule
    """
    _cleanup_existing_schedule(advance_settings)


def _create_or_update_schedule(advance_settings, hours: int):
    """
    Create or update the sync schedule
    """
    next_run = datetime.now() + timedelta(hours=hours)

    schedule, _ = Schedule.objects.update_or_create(
        func='apps.workspaces.tasks.run_import_export',
        args='{}'.format(advance_settings.workspace_id),
        defaults={
            'schedule_type': Schedule.MINUTES,
            'minutes': hours * 60,
            'next_run': next_run
        }
    )
    advance_settings.schedule = schedule
    advance_settings.save()


def _cleanup_existing_schedule(advance_settings):
    """
    Remove existing schedule if it exists
    """
    if advance_settings.schedule:
        schedule = advance_settings.schedule
        advance_settings.schedule = None
        advance_settings.save()
        schedule.delete()


def export_to_sage300(workspace_id: int, triggered_by: ExpenseImportSourceEnum, accounting_export_filters: dict = {}):
    """
    Function to export expenses to Sage 300
    """
    # Retrieve export settings for the given workspace
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)

    accounting_summary = AccountingExportSummary.objects.get(workspace_id=workspace_id)
    advance_settings = AdvancedSetting.objects.filter(workspace_id=workspace_id).first()

    is_auto_export = False
    interval_hours = 0

    # Set the timestamp for the last export
    last_exported_at = datetime.now()

    # Flag to track if expenses are exported
    is_expenses_exported = False

    # Dictionary mapping export types to their corresponding export classes
    export_map = {
        'PURCHASE_INVOICE': ExportPurchaseInvoice(),
        'DIRECT_COST': ExportDirectCost()
    }

    # Check and export reimbursable expenses if configured
    if export_settings.reimbursable_expenses_export_type:
        # Get IDs of unreexported accounting exports for personal fund source
        accounting_export_ids = AccountingExport.objects.filter(
            fund_source='PERSONAL', exported_at__isnull=True, workspace_id=workspace_id, **accounting_export_filters).values_list('id', flat=True)

        if len(accounting_export_ids):
            # Set the flag indicating expenses are exported
            is_expenses_exported = True
            # Get the appropriate export class and trigger the export
            export = export_map[export_settings.reimbursable_expenses_export_type]
            export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours, triggered_by=triggered_by, run_in_rabbitmq_worker=triggered_by == ExpenseImportSourceEnum.WEBHOOK)

    # Check and export credit card expenses if configured
    if export_settings.credit_card_expense_export_type:
        # Get IDs of unreexported accounting exports for credit card fund source
        accounting_export_ids = AccountingExport.objects.filter(
            fund_source='CCC', exported_at__isnull=True, workspace_id=workspace_id, **accounting_export_filters).values_list('id', flat=True)

        if len(accounting_export_ids):
            # Set the flag indicating expenses are exported
            is_expenses_exported = True
            # Get the appropriate export class and trigger the export
            export = export_map[export_settings.credit_card_expense_export_type]
            export.trigger_export(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours, triggered_by=triggered_by, run_in_rabbitmq_worker=triggered_by == ExpenseImportSourceEnum.WEBHOOK)

    # Update the accounting summary if expenses are exported
    if is_expenses_exported:

        if advance_settings.schedule_is_enabled:
            accounting_summary.next_export_at = last_exported_at + timedelta(hours=advance_settings.interval_hours)

        accounting_summary.last_exported_at = last_exported_at
        accounting_summary.export_mode = 'MANUAL'
        accounting_summary.save()


def async_create_admin_subcriptions(workspace_id: int) -> None:
    """
    Create admin subscriptions
    :param workspace_id: workspace id
    :return: None
    """
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)
    payload = {
        'is_enabled': True,
        'webhook_url': '{}/workspaces/{}/fyle/webhook_callback/'.format(settings.API_URL, workspace_id),
        'subscribed_resources': [
            'EXPENSE',
            'REPORT',
            'CATEGORY',
            'PROJECT',
            'COST_CENTER',
            'EXPENSE_FIELD',
            'CORPORATE_CARD',
            'EMPLOYEE',
            'TAX_GROUP',
            'ORG_SETTING'
        ]
    }
    platform.subscriptions.post(payload)


def patch_integration_settings(workspace_id: int, is_token_expired: bool, errors: int = None):
    """
    Patch integration settings
    """

    refresh_token = FyleCredential.objects.get(workspace_id=workspace_id).refresh_token
    url = '{}/integrations/'.format(settings.INTEGRATIONS_SETTINGS_API)
    payload = {
        'tpa_name': 'Fyle Sage 300 Integration'
    }

    if errors is not None:
        payload['errors_count'] = errors

    if is_token_expired is not None:
        payload['is_token_expired'] = is_token_expired

    try:
        patch_request(url, payload, refresh_token)
    except Exception as error:
        logger.error(error, exc_info=True)
