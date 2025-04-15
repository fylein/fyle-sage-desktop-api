"""
All Tasks from which involve Fyle APIs

1. Import Reimbursable Expenses from Fyle
2. Import Credit Card Expenses from Fyle
"""
import logging
from datetime import datetime, timezone
from typing import Dict
from django.db import transaction

from fyle_integrations_platform_connector import PlatformConnector
from fyle_integrations_platform_connector.apis.expenses import Expenses as FyleExpenses
from fyle_accounting_library.fyle_platform.helpers import get_expense_import_states, filter_expenses_based_on_state, get_source_account_types_based_on_export_modules
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import ExportSetting, Workspace, FyleCredential
from apps.fyle.models import Expense, ExpenseFilter
from apps.fyle.helpers import construct_expense_filter_query
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


def import_expenses(workspace_id, accounting_export: AccountingExport = None, source_account_type: str = None, fund_source_key: str = None, is_state_change_event: bool = False, report_state: str = None, imported_from: ExpenseImportSourceEnum = None, accounting_export_id: int = None, report_id: str = None):
    """
    Common logic for importing expenses from Fyle
    :param accounting_export: Task log object
    :param workspace_id: workspace id
    :param source_account_type: Fyle source account type
    :param fund_source_key: Key for accessing fund source specific fields in ExportSetting
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

    last_synced_at = getattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", None)

    settled_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAYMENT_PROCESSING':
        settled_at_query_param = last_synced_at

    approved_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'APPROVED':
        approved_at_query_param = last_synced_at

    last_paid_at_query_param = None
    if not is_state_change_event and getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAID':
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
                    workspace_id=workspace_id,
                    triggered_by=imported_from
                )
            if credit_card_expense_objects:
                AccountingExport.create_accounting_export(
                    credit_card_expense_objects,
                    fund_source='CCC',
                    workspace_id=workspace_id,
                    triggered_by=imported_from
                )

    accounting_export.status = 'COMPLETE'
    accounting_export.detail = None

    accounting_export.save()


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
