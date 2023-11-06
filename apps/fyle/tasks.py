import logging
from datetime import datetime
from typing import List
import traceback
from django.db import transaction

from fyle_integrations_platform_connector import PlatformConnector
from fyle.platform.exceptions import NoPrivilegeError

from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import ExportSetting, Workspace, FyleCredential
from apps.fyle.models import Expense


SOURCE_ACCOUNT_MAP = {
    'PERSONAL': 'PERSONAL_CASH_ACCOUNT',
    'CCC': 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'
}

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def get_accounting_exports_and_fund_source(workspace_id: int):
    # Create or update an AccountingExport instance for the given workspace
    accounting_export, _ = AccountingExport.objects.update_or_create(
        workspace_id=workspace_id,
        type='FETCHING_EXPENSES',
        defaults={
            'status': 'IN_PROGRESS'
        }
    )

    # Retrieve the ExportSetting for the workspace
    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)

    # Initialize an empty list to store fund sources
    fund_source = []

    # Check if reimbursable_expenses_object is enabled in the export settings
    if export_setting.reimbursable_expenses_object:
        fund_source.append('PERSONAL')

    # Check if corporate_credit_card_expenses_object is enabled in the export settings
    if export_setting.corporate_credit_card_expenses_object:
        fund_source.append('CCC')

    # Return the AccountingExport instance and the list of fund sources
    return accounting_export, fund_source


def create_accounting_exports(workspace_id: int, fund_source: List[str], accounting_export: AccountingExport):
    """
    Create expense groups
    :param task_log: Task log object
    :param workspace_id: workspace id
    :param fund_source: expense fund source
    """
    try:
        with transaction.atomic():
            workspace = Workspace.objects.get(pk=workspace_id)

            last_synced_at = workspace.last_synced_at
            ccc_last_synced_at = workspace.ccc_last_synced_at
            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)

            export_setting = ExportSetting.objects.get(workspace_id=workspace_id)

            platform = PlatformConnector(fyle_credentials)
            source_account_type = []

            for source in fund_source:
                source_account_type.append(SOURCE_ACCOUNT_MAP[source])

            filter_credit_expenses = False

            expenses = []
            reimbursable_expense_count = 0

            if 'PERSONAL' in fund_source:
                expenses.extend(platform.expenses.get(
                    source_account_type=['PERSONAL_CASH_ACCOUNT'],
                    state=export_setting.reimbursable_expense_state,
                    settled_at=last_synced_at if export_setting.reimbursable_expense_state == 'PAYMENT_PROCESSING' else None,
                    filter_credit_expenses=filter_credit_expenses,
                    last_paid_at=last_synced_at if export_setting.reimbursable_expense_state == 'PAID' else None
                ))

            if expenses:
                workspace.last_synced_at = datetime.now()
                reimbursable_expense_count += len(expenses)

            if 'CCC' in fund_source:
                expenses.extend(platform.expenses.get(
                    source_account_type=['PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
                    state=export_setting.ccc_expense_state,
                    settled_at=ccc_last_synced_at if export_setting.credit_card_expense_state == 'PAYMENT_PROCESSING' else None,
                    approved_at=ccc_last_synced_at if export_setting.credit_card_expense_state == 'APPROVED' else None,
                    filter_credit_expenses=filter_credit_expenses,
                    last_paid_at=ccc_last_synced_at if export_setting.credit_card_expense_state == 'PAID' else None
                ))

            if len(expenses) != reimbursable_expense_count:
                workspace.ccc_last_synced_at = datetime.now()

            workspace.save()

            expense_objects = Expense.create_expense_objects(expenses, workspace_id)

            AccountingExport.create_expense_groups_by_report_id_fund_source(
                expense_objects, workspace_id
            )

            accounting_export.status = 'COMPLETE'
            accounting_export.save()

    except NoPrivilegeError:
        logger.info('Invalid Fyle Credentials / Admin is disabled')
        accounting_export.detail = {
            'message': 'Invalid Fyle Credentials / Admin is disabled'
        }
        accounting_export.status = 'FAILED'
        accounting_export.save()

    except FyleCredential.DoesNotExist:
        logger.info('Fyle credentials not found %s', workspace_id)
        accounting_export.detail = {
            'message': 'Fyle credentials do not exist in workspace'
        }
        accounting_export.status = 'FAILED'
        accounting_export.save()

    except Exception:
        error = traceback.format_exc()
        accounting_export.detail = {
            'error': error
        }
        accounting_export.status = 'FATAL'
        accounting_export.save()
        logger.exception('Something unexpected happened workspace_id: %s %s', accounting_export.workspace_id, accounting_export.detail)
