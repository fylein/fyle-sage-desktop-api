"""
All Tasks from which involve Fyle APIs

1. Import Reimbursable Expenses from Fyle
2. Import Credit Card Expenses from Fyle
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List

from django.db import transaction
from django.db.models import Q
from django.utils.module_loading import import_string

from fyle_integrations_platform_connector import PlatformConnector
from fyle_integrations_platform_connector.apis.expenses import Expenses as FyleExpenses
from fyle_accounting_library.fyle_platform.helpers import get_expense_import_states, filter_expenses_based_on_state, get_source_account_types_based_on_export_modules
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_library.fyle_platform.branding import feature_configuration

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.workspaces.models import ExportSetting, Workspace, FyleCredential, AdvancedSetting
from apps.fyle.models import Expense, ExpenseFilter
from apps.fyle.helpers import __bulk_update_expenses, construct_expense_filter_query
from apps.fyle.exceptions import handle_exceptions

SOURCE_ACCOUNT_MAP = {
    'PERSONAL': 'PERSONAL_CASH_ACCOUNT',
    'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
}

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_filtered_expenses(workspace: int, expense_objects: list, expense_filters: list):
    """
    function to get filtered expense objects
    """

    expenses_object_ids = [expense_object.id for expense_object in expense_objects]
    final_query = construct_expense_filter_query(expense_filters)

    Expense.objects.filter(
        final_query,
        id__in=expenses_object_ids,
        accountingexport__isnull=True,
        org_id=workspace.org_id
    ).update(is_skipped=True, updated_at=datetime.now(timezone.utc))

    filtered_expenses = Expense.objects.filter(
        is_skipped=False,
        id__in=expenses_object_ids,
        accountingexport__isnull=True,
        org_id=workspace.org_id
    )

    return filtered_expenses


def import_expenses(workspace_id, accounting_export: AccountingExport = None, source_account_type: str = None, fund_source_key: str = None, is_state_change_event: bool = False, report_state: str = None, imported_from: ExpenseImportSourceEnum = None, accounting_export_id: int = None, report_id: str = None, trigger_export: bool = False, triggered_by: ExpenseImportSourceEnum = None):
    """
    Common logic for importing expenses from Fyle
    :param accounting_export: Task log object
    :param workspace_id: workspace id
    :param source_account_type: Fyle source account type
    :param fund_source_key: Key for accessing fund source specific fields in ExportSetting
    :param trigger_export: trigger export - will be true for webhook calls that are state change events (i.e. report state changes)
    :param triggered_by: triggered by
    """
    if accounting_export_id:
        accounting_export = AccountingExport.objects.get(id=accounting_export_id, workspace_id=workspace_id)
        accounting_export.status = 'IN_PROGRESS'
        accounting_export.save()

    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    import_states = get_expense_import_states(export_settings, integration_type='sage_desktop')

    # Don't call API if report state is not in import states, for example customer configured to import only PAID reports but webhook is triggered for APPROVED report (this is only for is_state_change_event webhook calls)
    workspace = Workspace.objects.get(pk=workspace_id)
    if is_state_change_event and report_state and report_state not in import_states:
        return

    fund_source_map = {
        'PERSONAL': 'reimbursable',
        'CCC': 'credit_card'
    }

    last_synced_at = getattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", None) if imported_from != ExpenseImportSourceEnum.CONFIGURATION_UPDATE else None

    settled_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAYMENT_PROCESSING' and imported_from != ExpenseImportSourceEnum.CONFIGURATION_UPDATE:
        settled_at_query_param = last_synced_at

    approved_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'APPROVED' and imported_from != ExpenseImportSourceEnum.CONFIGURATION_UPDATE:
        approved_at_query_param = last_synced_at

    last_paid_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAID' and imported_from != ExpenseImportSourceEnum.CONFIGURATION_UPDATE:
        last_paid_at_query_param = last_synced_at

    import_states_query_param = None
    state_query_param = None
    if is_state_change_event:
        import_states_query_param = import_states
    else:
        state_query_param = getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state")

    source_account_type_query_param = None
    if is_state_change_event:
        source_account_types = get_source_account_types_based_on_export_modules(export_settings.reimbursable_expenses_export_type, export_settings.credit_card_expense_export_type)
        source_account_type_query_param = source_account_types
    else:
        source_account_type_query_param = [source_account_type]

    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials)

    expenses = platform.expenses.get(
        source_account_type=source_account_type_query_param,
        state=state_query_param,
        settled_at=settled_at_query_param,
        approved_at=approved_at_query_param,
        filter_credit_expenses=False,
        last_paid_at=last_paid_at_query_param,
        import_states=import_states_query_param,
        report_id=report_id if report_id else None
    )

    if is_state_change_event:
        expenses = filter_expenses_based_on_state(expenses, export_settings, 'sage_desktop')

    if expenses:
        with transaction.atomic():
            if not is_state_change_event:
                setattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", datetime.now())
                if imported_from != ExpenseImportSourceEnum.CONFIGURATION_UPDATE:
                    workspace.save()

            expense_objects = Expense.create_expense_objects(expenses, workspace_id, imported_from=imported_from)

            expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace_id).order_by('rank')
            if expense_filters:
                expense_objects = get_filtered_expenses(workspace, expense_objects, expense_filters)

            reimbursable_expense_objects = list(filter(lambda expense: expense.fund_source == 'PERSONAL', expense_objects))
            credit_card_expense_objects = list(filter(lambda expense: expense.fund_source == 'CCC', expense_objects))

            if reimbursable_expense_objects:
                AccountingExport.create_accounting_export(
                    reimbursable_expense_objects,
                    fund_source='PERSONAL',
                    workspace_id=workspace_id
                )
            if credit_card_expense_objects:
                AccountingExport.create_accounting_export(
                    credit_card_expense_objects,
                    fund_source='CCC',
                    workspace_id=workspace_id
                )

    if accounting_export:
        accounting_export.status = 'COMPLETE'
        accounting_export.detail = None

        accounting_export.save()

    if trigger_export:
        # Trigger export immediately for customers who have enabled real time export
        is_real_time_export_enabled = AdvancedSetting.objects.filter(workspace_id=workspace.id, is_real_time_export_enabled=True).exists()

        # Allow real time export if it's supported for the branded app and setting is enabled
        if is_real_time_export_enabled and feature_configuration.feature.real_time_export_1hr_orgs:
            logger.info(f'Exporting expenses for workspace {workspace.id} with report id {report_id}, triggered by {imported_from}')
            import_string('apps.workspaces.tasks.export_to_sage300')(workspace_id=workspace_id, triggered_by=triggered_by, accounting_export_filters={'expenses__report_id': report_id})


@handle_exceptions
def import_reimbursable_expenses(workspace_id, accounting_export: AccountingExport, imported_from: ExpenseImportSourceEnum):
    """
    Import reimbursable expenses from Fyle
    :param accounting_export: Accounting Export object
    :param workspace_id: workspace id
    """
    import_expenses(workspace_id=workspace_id, accounting_export=accounting_export, source_account_type='PERSONAL_CASH_ACCOUNT', fund_source_key='PERSONAL', imported_from=imported_from)


@handle_exceptions
def import_credit_card_expenses(workspace_id, accounting_export: AccountingExport, imported_from: ExpenseImportSourceEnum):
    """
    Import credit card expenses from Fyle
    :param accounting_export: AccountingExport object
    :param workspace_id: workspace id
    """
    import_expenses(workspace_id=workspace_id, accounting_export=accounting_export, source_account_type='PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', fund_source_key='CCC', imported_from=imported_from)


def update_non_exported_expenses(data: Dict) -> None:
    """
    To update expenses not in COMPLETE, IN_PROGRESS state
    """
    org_id = data['org_id']
    expense_id = data['id']
    workspace = Workspace.objects.get(org_id=org_id)
    expense = Expense.objects.filter(workspace_id=workspace.id, expense_id=expense_id).first()

    if expense:
        accounting_export = AccountingExport.objects.filter(
            workspace_id=workspace.id,
            expenses=expense,
            status__in=['EXPORT_READY', 'FAILED', 'FATAL']
        ).first()

        if accounting_export:
            expense_obj = []
            expense_obj.append(data)
            expense_objects = FyleExpenses().construct_expense_object(expense_obj, expense.workspace_id)
            Expense.create_expense_objects(
                expense_objects, expense.workspace_id, skip_update=True
            )


def mark_expenses_as_skipped(final_query: Q, expenses_object_ids: List, workspace: Workspace) -> List[Expense]:
    """
    Mark expenses as skipped in bulk
    :param final_query: final query
    :param expenses_object_ids: expenses object ids
    :param workspace: workspace object
    :return: List of skipped expense objects
    """
    expenses_to_be_skipped = Expense.objects.filter(
        final_query,
        id__in=expenses_object_ids,
        org_id=workspace.org_id,
        is_skipped=False
    )
    skipped_expenses_list = list(expenses_to_be_skipped)
    expense_to_be_updated = []
    for expense in expenses_to_be_skipped:
        expense_to_be_updated.append(
            Expense(
                id=expense.id,
                is_skipped=True,
            )
        )

    if expense_to_be_updated:
        __bulk_update_expenses(expense_to_be_updated)

    # Return the updated expense objects
    return skipped_expenses_list


def re_run_skip_export_rule(workspace: Workspace) -> None:
    """
    Skip expenses before export
    :param workspace_id: Workspace id
    :return: None
    """
    expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace.id).order_by('rank')
    if expense_filters:
        filtered_expense_query = construct_expense_filter_query(expense_filters)
        # Get all expenses matching the filter query, excluding those in COMPLETE state
        expenses = Expense.objects.filter(
            filtered_expense_query, workspace_id=workspace.id, is_skipped=False, accountingexport__exported_at__isnull=True
        )
        expense_ids = list(expenses.values_list('id', flat=True))
        skipped_expenses = mark_expenses_as_skipped(
            filtered_expense_query,
            expense_ids,
            workspace
        )
        if skipped_expenses:
            accounting_exports = AccountingExport.objects.filter(exported_at__isnull=True, workspace_id=workspace.id, expenses__in=skipped_expenses)
            deleted_failed_accounting_export_count = 0
            deleted_total_accounting_export_count = 0
            for accounting_export in accounting_exports:
                if accounting_export.status != 'COMPLETE':
                    deleted_failed_accounting_export_count += 1

                error = Error.objects.filter(
                    workspace_id=workspace.id,
                    accounting_export_id=accounting_export.id
                ).first()
                if error:
                    logger.info('Deleting Sage300 error for accounting export %s before export', accounting_export.id)
                    error.delete()

                accounting_export.expenses.remove(*skipped_expenses)
                if not accounting_export.expenses.exists():
                    logger.info('Deleting empty accounting export %s before export', accounting_export.id)
                    accounting_export.delete()
                    deleted_total_accounting_export_count += 1

            last_export_detail = AccountingExportSummary.objects.filter(workspace_id=workspace.id).first()
            if last_export_detail:
                last_export_detail.failed_accounting_export_count = max(
                    0,
                    (last_export_detail.failed_accounting_export_count or 0) - deleted_failed_accounting_export_count
                )
                last_export_detail.total_accounting_export_count = max(
                    0,
                    (last_export_detail.total_accounting_export_count or 0) - deleted_total_accounting_export_count
                )
                last_export_detail.save()
