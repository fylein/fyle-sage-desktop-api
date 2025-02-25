"""
All Tasks from which involve Fyle APIs

1. Import Reimbursable Expenses from Fyle
2. Import Credit Card Expenses from Fyle
"""
import logging
from datetime import datetime
from typing import Dict
from django.db import transaction
from django.db.models import Q
from fyle_integrations_platform_connector import PlatformConnector
from fyle_integrations_platform_connector.apis.expenses import Expenses as FyleExpenses

from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import ExportSetting, LastExportDetail, Workspace, FyleCredential
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
    ).update(is_skipped=True)

    filtered_expenses = Expense.objects.filter(
        is_skipped=False,
        id__in=expenses_object_ids,
        accountingexport__isnull=True,
        org_id=workspace.org_id
    )

    return filtered_expenses


def import_expenses(workspace_id, accounting_export: AccountingExport, source_account_type, fund_source_key):
    """
    Common logic for importing expenses from Fyle
    :param accounting_export: Task log object
    :param workspace_id: workspace id
    :param source_account_type: Fyle source account type
    :param fund_source_key: Key for accessing fund source specific fields in ExportSetting
    """

    fund_source_map = {
        'PERSONAL': 'reimbursable',
        'CCC': 'credit_card'
    }
    export_settings = ExportSetting.objects.get(workspace_id=workspace_id)
    workspace = Workspace.objects.get(pk=workspace_id)
    last_synced_at = getattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", None)
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

    platform = PlatformConnector(fyle_credentials)

    expenses = platform.expenses.get(
        source_account_type=[source_account_type],
        state=getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state"),
        settled_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAYMENT_PROCESSING' else None,
        approved_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'APPROVED' else None,
        filter_credit_expenses=False,
        last_paid_at=last_synced_at if getattr(export_settings, f"{fund_source_map.get(fund_source_key)}_expense_state") == 'PAID' else None
    )

    if expenses:
        with transaction.atomic():

            setattr(workspace, f"{fund_source_map.get(fund_source_key)}_last_synced_at", datetime.now())
            workspace.save()
            expense_objects = Expense.create_expense_objects(expenses, workspace_id)

            expense_filters = ExpenseFilter.objects.filter(workspace_id=workspace_id).order_by('rank')
            if expense_filters:
                expense_objects = get_filtered_expenses(workspace, expense_objects, expense_filters)

            AccountingExport.create_accounting_export(
                expense_objects,
                fund_source=fund_source_key,
                workspace_id=workspace_id
            )

    accounting_export.status = 'COMPLETE'
    accounting_export.detail = None

    accounting_export.save()


@handle_exceptions
def import_reimbursable_expenses(workspace_id, accounting_export: AccountingExport):
    """
    Import reimbursable expenses from Fyle
    :param accounting_export: Accounting Export object
    :param workspace_id: workspace id
    """
    import_expenses(workspace_id, accounting_export, 'PERSONAL_CASH_ACCOUNT', 'PERSONAL')


@handle_exceptions
def import_credit_card_expenses(workspace_id, accounting_export: AccountingExport):
    """
    Import credit card expenses from Fyle
    :param accounting_export: AccountingExport object
    :param workspace_id: workspace id
    """
    import_expenses(workspace_id, accounting_export, 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', 'CCC')


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
            filtered_expense_query,
            workspace_id=workspace.id,
            is_skipped=False
        ).exclude(
            ~Q(accounting_export_summary={}),
            accounting_export_summary__state='COMPLETE'
        )
        expense_ids = list(expenses.values_list('id', flat=True))
        skipped_expenses = get_filtered_expenses(
            filtered_expense_query,
            expense_ids,
            workspace
        )
        if skipped_expenses:
            accounting_exports = AccountingExport.objects.filter(exported_at__isnull=True, workspace_id=workspace.id)
            deleted_failed_expense_groups_count = 0
            for accounting_export in accounting_exports:
                if accounting_export.status != 'COMPLETE':
                    deleted_failed_expense_groups_count += 1

                error = Error.objects.filter(
                    workspace_id=workspace.id,
                    accounting_export_id=accounting_export.id
                ).first()
                if error:
                    logger.info('Deleting error for accounting export %s before export', accounting_export.id)
                    error.delete()

                # deleting accounting export after deleting errors
                logger.info('Deleting accounting export %s before export', accounting_export.id)
                accounting_export.delete()

            last_export_detail = LastExportDetail.objects.filter(workspace_id=workspace.id, failed_expense_groups_count__gt=0).first()
            if last_export_detail and deleted_failed_expense_groups_count > 0:
                last_export_detail.failed_expense_groups_count = max(
                    0,
                    last_export_detail.failed_expense_groups_count - deleted_failed_expense_groups_count
                )
                last_export_detail.total_expense_groups_count = max(
                    0,
                    last_export_detail.total_expense_groups_count - deleted_failed_expense_groups_count
                )
                last_export_detail.save()
