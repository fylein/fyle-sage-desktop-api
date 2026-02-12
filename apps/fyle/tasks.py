"""
All Tasks from which involve Fyle APIs

1. Import Reimbursable Expenses from Fyle
2. Import Credit Card Expenses from Fyle
"""
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from django.db import transaction
from django.db.models import Q, Count
from django.utils.module_loading import import_string
from django_q.models import Schedule
from django_q.tasks import schedule

from fyle_integrations_platform_connector import PlatformConnector
from fyle_integrations_platform_connector.apis.expenses import Expenses as FyleExpenses
from fyle_accounting_library.fyle_platform.helpers import get_expense_import_states, filter_expenses_based_on_state, get_source_account_types_based_on_export_modules
from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum
from fyle_accounting_library.fyle_platform.branding import feature_configuration

from apps.accounting_exports.models import AccountingExport, AccountingExportSummary, Error
from apps.workspaces.models import ExportSetting, Workspace, FyleCredential, AdvancedSetting
from apps.fyle.models import Expense, ExpenseFilter, SOURCE_ACCOUNT_MAP
from apps.fyle.helpers import __bulk_update_expenses, construct_expense_filter_query
from apps.fyle.exceptions import handle_exceptions
from apps.workspaces.helpers import construct_filter_for_affected_accounting_exports
from sage_desktop_api.logging_middleware import get_logger

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

            # Handle fund source changes for state change events (report state changes)
            if is_state_change_event and report_id:
                try:
                    expenses_count = Expense.objects.filter(workspace_id=workspace_id, report_id=report_id).count()
                    if expenses_count > 0 and report_state in ('APPROVED', 'ADMIN_APPROVED'):
                        logger.info("Handling expense fund source change for workspace_id: %s, report_id: %s", workspace_id, report_id)
                        handle_expense_fund_source_change(workspace_id, report_id, platform)
                except Exception as e:
                    logger.exception("Error handling expense fund source change for workspace_id: %s, report_id: %s | ERROR: %s", workspace_id, report_id, e)

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
            logger.info('Exporting expenses for workspace %s with report id %s, triggered by %s', workspace.id, report_id, imported_from)
            import_string('apps.workspaces.tasks.export_to_sage300')(workspace_id=workspace_id, triggered_by=triggered_by, accounting_export_filters={'expenses__report_id': report_id})


@handle_exceptions
def import_reimbursable_expenses(workspace_id, accounting_export, imported_from: ExpenseImportSourceEnum):
    """
    Import reimbursable expenses from Fyle
    :param accounting_export: Accounting Export object or ID
    :param workspace_id: workspace id
    """
    # Handle both object and ID for RabbitMQ compatibility
    if isinstance(accounting_export, int):
        accounting_export = AccountingExport.objects.get(id=accounting_export)

    import_expenses(workspace_id=workspace_id, accounting_export=accounting_export, source_account_type='PERSONAL_CASH_ACCOUNT', fund_source_key='PERSONAL', imported_from=imported_from)


@handle_exceptions
def import_credit_card_expenses(workspace_id, accounting_export, imported_from: ExpenseImportSourceEnum):
    """
    Import credit card expenses from Fyle
    :param accounting_export: AccountingExport object or ID
    :param workspace_id: workspace id
    """
    # Handle both object and ID for RabbitMQ compatibility
    if isinstance(accounting_export, int):
        accounting_export = AccountingExport.objects.get(id=accounting_export)

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

            old_fund_source = expense.fund_source
            new_fund_source = SOURCE_ACCOUNT_MAP[expense_objects[0]['source_account_type']]

            Expense.create_expense_objects(
                expense_objects, expense.workspace_id, skip_update=True
            )

            if old_fund_source != new_fund_source:
                logger.info("Fund source changed for expense %s from %s to %s in workspace %s", expense.id, old_fund_source, new_fund_source, expense.workspace_id)
                handle_fund_source_changes_for_expense_ids(
                    workspace_id=expense.workspace_id,
                    changed_expense_ids=[expense.id],
                    report_id=expense.report_id,
                    affected_fund_source_expense_ids={old_fund_source: [expense.id]}
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


def handle_expense_fund_source_change(workspace_id: int, report_id: str, platform: PlatformConnector) -> None:
    """
    Handle expense fund source change
    :param workspace_id: Workspace id
    :param report_id: Report id
    :param platform: Platform connector
    :return: None
    """
    expenses = platform.expenses.get(
        source_account_type=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
        report_id=report_id,
        filter_credit_expenses=False
    )

    expenses_to_update = []
    expense_ids_changed = []
    expenses_in_db = Expense.objects.filter(workspace_id=workspace_id, report_id=report_id).values_list('expense_id', 'fund_source', 'id')
    expense_id_fund_source_map = {
        expense[0]: {
            'fund_source': expense[1],
            'id': expense[2]
        }
        for expense in expenses_in_db
    }

    affected_fund_source_expense_ids = {
        'PERSONAL': [],
        'CCC': []
    }

    for expense in expenses:
        if expense['id'] in expense_id_fund_source_map:
            new_expense_fund_source = SOURCE_ACCOUNT_MAP[expense['source_account_type']]
            old_expense_fund_source = expense_id_fund_source_map[expense['id']]['fund_source']
            if new_expense_fund_source != old_expense_fund_source:
                logger.info("Expense Fund Source changed for expense %s from %s to %s", expense['id'], old_expense_fund_source, new_expense_fund_source)
                expenses_to_update.append(expense)
                expense_ids_changed.append(expense_id_fund_source_map[expense['id']]['id'])
                affected_fund_source_expense_ids[old_expense_fund_source].append(expense_id_fund_source_map[expense['id']]['id'])

    if expenses_to_update:
        logger.info("Updating Fund Source Change for expenses with report_id %s in workspace %s | COUNT %s", report_id, workspace_id, len(expenses_to_update))
        Expense.create_expense_objects(expenses=expenses_to_update, workspace_id=workspace_id, skip_update=False)
        handle_fund_source_changes_for_expense_ids(workspace_id=workspace_id, changed_expense_ids=expense_ids_changed, report_id=report_id, affected_fund_source_expense_ids=affected_fund_source_expense_ids)


def handle_fund_source_changes_for_expense_ids(workspace_id: int, changed_expense_ids: List[int], report_id: str, affected_fund_source_expense_ids: dict, task_name: str = None) -> None:
    """
    Main entry point for handling fund_source changes for expense ids
    :param workspace_id: workspace id
    :param changed_expense_ids: List of expense IDs whose fund_source changed
    :param report_id: Report id
    :param affected_fund_source_expense_ids: Dict of affected fund sources and their expense ids
    :param task_name: Name of the task to clean up
    :return: None
    """
    worker_logger = get_logger()

    filter_for_affected_accounting_exports = construct_filter_for_affected_accounting_exports(
        workspace_id=workspace_id,
        report_id=report_id,
        changed_expense_ids=changed_expense_ids,
        affected_fund_source_expense_ids=affected_fund_source_expense_ids
    )

    with transaction.atomic():
        affected_exports = AccountingExport.objects.filter(
            filter_for_affected_accounting_exports,
            workspace_id=workspace_id,
            exported_at__isnull=True
        ).annotate(
            expense_count=Count('expenses')
        ).distinct()

        if not affected_exports:
            worker_logger.info("No accounting exports found for changed expenses: %s in workspace %s", changed_expense_ids, workspace_id)
            return

        affected_expense_ids = list(affected_exports.values_list('expenses__id', flat=True))
        are_all_accounting_exports_exported = True

        for export in affected_exports:
            worker_logger.info("Processing fund source change for accounting export %s with %s expenses in workspace %s", export.id, export.expense_count, workspace_id)
            is_accounting_export_processed = process_accounting_export_for_fund_source_update(
                accounting_export=export,
                changed_expense_ids=changed_expense_ids,
                workspace_id=workspace_id,
                report_id=report_id,
                affected_fund_source_expense_ids=affected_fund_source_expense_ids
            )

            if not is_accounting_export_processed:
                are_all_accounting_exports_exported = False

        if are_all_accounting_exports_exported:
            worker_logger.info("All accounting exports are exported, proceeding with recreation of accounting exports for changed expense ids %s in workspace %s", changed_expense_ids, workspace_id)
            recreate_accounting_exports(workspace_id=workspace_id, expense_ids=affected_expense_ids)
            if task_name:
                cleanup_scheduled_task(task_name=task_name, workspace_id=workspace_id)
        else:
            worker_logger.info("Not all accounting exports are exported, scheduling task for fund source changes later for workspace %s", workspace_id)
            schedule_task_for_expense_group_fund_source_change(
                changed_expense_ids=changed_expense_ids,
                workspace_id=workspace_id,
                report_id=report_id,
                affected_fund_source_expense_ids=affected_fund_source_expense_ids
            )


def process_accounting_export_for_fund_source_update(
    accounting_export: AccountingExport,
    changed_expense_ids: List[int],
    workspace_id: int,
    report_id: str,
    affected_fund_source_expense_ids: dict
) -> bool:
    """
    Process individual accounting export based on export state
    :param accounting_export: Accounting export
    :param changed_expense_ids: List of expense IDs whose fund_source changed
    :param workspace_id: Workspace id
    :param report_id: Report id
    :param affected_fund_source_expense_ids: Dict of affected fund sources and their expense ids
    :return: True if processed, False if already exported
    """
    if accounting_export.exported_at:
        logger.info("Accounting export %s already exported, cannot modify", accounting_export.id)
        return False

    if accounting_export.status in ['ENQUEUED', 'IN_PROGRESS', 'EXPORT_QUEUED']:
        logger.info("Accounting export %s is in %s state, skipping processing", accounting_export.id, accounting_export.status)
        return False

    if accounting_export.status == 'COMPLETE':
        logger.info("Skipping accounting export %s - already exported successfully", accounting_export.id)
        return False

    logger.info("Proceeding with processing for accounting export %s in workspace %s", accounting_export.id, workspace_id)
    delete_accounting_export_and_related_data(accounting_export=accounting_export, workspace_id=workspace_id)
    return True


def delete_accounting_export_and_related_data(accounting_export: AccountingExport, workspace_id: int) -> None:
    """
    Delete accounting export and all related data safely
    :param accounting_export: Accounting export
    :param workspace_id: Workspace id
    :return: None
    """
    export_id = accounting_export.id

    # Delete errors
    errors_deleted = Error.objects.filter(
        accounting_export_id=export_id,
        workspace_id=workspace_id
    ).delete()
    logger.info("Deleted %s error logs for accounting export %s in workspace %s", errors_deleted[0], export_id, workspace_id)

    # Delete the accounting export (this will also delete relationships)
    accounting_export.delete()
    logger.info("Deleted accounting export %s in workspace %s", export_id, workspace_id)


def recreate_accounting_exports(workspace_id: int, expense_ids: List[int]) -> None:
    """
    Recreate accounting exports using standard grouping logic
    :param workspace_id: Workspace id
    :param expense_ids: List of expense IDs
    :return: None
    """
    logger.info("Recreating accounting exports for %s expenses in workspace %s", len(expense_ids), workspace_id)

    expenses = Expense.objects.filter(
        id__in=expense_ids,
        accountingexport__exported_at__isnull=True,
        workspace_id=workspace_id
    )

    if not expenses:
        logger.warning("No expenses found for recreation: %s in workspace %s", expense_ids, workspace_id)
        return

    export_setting = ExportSetting.objects.get(workspace_id=workspace_id)

    # Skip reimbursable expenses if reimbursable expense settings is not configured
    if not export_setting.reimbursable_expenses_export_type:
        reimbursable_expense_ids = [e.id for e in expenses if e.fund_source == 'PERSONAL']

        if reimbursable_expense_ids:
            expenses = [e for e in expenses if e.id not in reimbursable_expense_ids]
            # Mark these expenses as skipped
            Expense.objects.filter(id__in=reimbursable_expense_ids).update(is_skipped=True)

    # Skip corporate credit card expenses if corporate credit card expense settings is not configured
    if not export_setting.credit_card_expense_export_type:
        ccc_expense_ids = [e.id for e in expenses if e.fund_source == 'CCC']

        if ccc_expense_ids:
            expenses = [e for e in expenses if e.id not in ccc_expense_ids]
            # Mark these expenses as skipped
            Expense.objects.filter(id__in=ccc_expense_ids).update(is_skipped=True)

    expense_objects = expenses
    filters = ExpenseFilter.objects.filter(workspace_id=workspace_id).order_by('rank')

    if filters:
        workspace = Workspace.objects.get(id=workspace_id)
        expense_objects = get_filtered_expenses(workspace, list(expenses), filters)

    # Group by fund source and create accounting exports
    reimbursable_expenses = [exp for exp in expense_objects if exp.fund_source == 'PERSONAL']
    credit_card_expenses = [exp for exp in expense_objects if exp.fund_source == 'CCC']

    if reimbursable_expenses:
        logger.info("Creating accounting exports for %s reimbursable expenses", len(reimbursable_expenses))
        AccountingExport.create_accounting_export(
            reimbursable_expenses,
            fund_source='PERSONAL',
            workspace_id=workspace_id
        )

    if credit_card_expenses:
        logger.info("Creating accounting exports for %s credit card expenses", len(credit_card_expenses))
        AccountingExport.create_accounting_export(
            credit_card_expenses,
            fund_source='CCC',
            workspace_id=workspace_id
        )

    logger.info("Successfully recreated accounting exports for %s expenses in workspace %s", len(expense_ids), workspace_id)


def schedule_task_for_expense_group_fund_source_change(changed_expense_ids: List[int], workspace_id: int, report_id: str, affected_fund_source_expense_ids: dict) -> None:
    """
    Schedule expense group for later processing when task logs are no longer active
    :param changed_expense_ids: List of expense IDs whose fund_source changed
    :param workspace_id: Workspace id
    :param report_id: Report id
    :param affected_fund_source_expense_ids: Dict of affected fund sources and their expense ids
    :return: None
    """
    logger.info("Scheduling for later processing for changed expense ids %s in workspace %s", changed_expense_ids, workspace_id)

    # generate some random string to avoid duplicate tasks
    hashed_name = hashlib.md5(str(changed_expense_ids).encode('utf-8')).hexdigest()[0:6]

    # Check if there's already a scheduled task for this expense group to avoid duplicates
    task_name = f'fund_source_change_retry_{hashed_name}_{workspace_id}'
    existing_schedule = Schedule.objects.filter(
        func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        name=task_name
    ).first()

    if existing_schedule:
        logger.info("Task already scheduled for changed expense ids %s in workspace %s", changed_expense_ids, workspace_id)
        return

    schedule_time = datetime.now() + timedelta(minutes=5)

    schedule(
        'apps.fyle.tasks.handle_fund_source_changes_for_expense_ids',
        workspace_id,
        changed_expense_ids,
        report_id,
        affected_fund_source_expense_ids,
        task_name,
        repeats=10,  # 10 retries
        schedule_type='M',  # Minute
        minutes=5,  # 5 minutes delay
        timeout=300,  # 5 minutes timeout
        next_run=schedule_time,
        name=task_name
    )

    logger.info("Scheduled delayed processing for changed expense ids %s in workspace %s with name %s", changed_expense_ids, workspace_id, task_name)


def cleanup_scheduled_task(task_name: str, workspace_id: int) -> None:
    """
    Clean up scheduled task
    :param task_name: Name of the task to clean up
    :param workspace_id: Workspace id
    :return: None
    """
    logger.info("Cleaning up scheduled task %s in workspace %s", task_name, workspace_id)

    schedule_obj = Schedule.objects.filter(name=task_name, func='apps.fyle.tasks.handle_fund_source_changes_for_expense_ids').first()
    if schedule_obj:
        schedule_obj.delete()
        logger.info("Cleaned up scheduled task: %s", task_name)
    else:
        logger.info("No scheduled task found to clean up: %s", task_name)


def handle_org_setting_updated(workspace_id: int, org_settings: dict) -> None:
    """
    Update regional date setting on org setting updated
    :param workspace_id: Workspace id
    :param org_settings: Org settings
    :return: None
    """
    worker_logger = get_logger()
    worker_logger.info("Handling org settings update for workspace %s", workspace_id)

    workspace = Workspace.objects.get(id=workspace_id)
    workspace.org_settings = {
        'regional_settings': org_settings.get('regional_settings', {})
    }
    workspace.save(update_fields=['org_settings', 'updated_at'])
    worker_logger.info("Updated org settings for workspace %s", workspace.id)


def handle_expense_report_change(expense_data: dict, action_type: str) -> None:
    """
    Handle expense report changes (EJECTED_FROM_REPORT, ADDED_TO_REPORT)
    :param expense_data: Expense data from webhook
    :param action_type: Type of action (EJECTED_FROM_REPORT or ADDED_TO_REPORT)
    :return: None
    """
    worker_logger = get_logger()
    org_id = expense_data['org_id']
    expense_id = expense_data['id']
    workspace = Workspace.objects.get(org_id=org_id)

    if action_type == 'ADDED_TO_REPORT':
        report_id = expense_data.get('report_id')

        worker_logger.info("Processing ADDED_TO_REPORT for expense %s in workspace %s, report_id: %s", expense_id, workspace.id, report_id)
        _delete_accounting_exports_for_report(report_id, workspace)
        return

    elif action_type == 'EJECTED_FROM_REPORT':
        expense = Expense.objects.filter(workspace_id=workspace.id, expense_id=expense_id).first()

        if not expense:
            worker_logger.warning("Expense %s not found in workspace %s for action %s", expense_id, workspace.id, action_type)
            return

        accounting_export = AccountingExport.objects.filter(
            expenses=expense,
            workspace_id=workspace.id,
            exported_at__isnull=False
        ).first()

        if accounting_export:
            worker_logger.info("Skipping %s for expense %s as it's part of exported accounting export %s", action_type, expense_id, accounting_export.id)
            return

        worker_logger.info("Processing %s for expense %s in workspace %s", action_type, expense_id, workspace.id)
        _handle_expense_ejected_from_report(expense, expense_data, workspace)


def _delete_accounting_exports_for_report(report_id: str, workspace: Workspace) -> None:
    """
    Delete all non-exported accounting exports for a report
    When expenses are added to a report, the report goes to SUBMITTED state which is not importable.
    This function deletes all accounting exports for the report so they can be recreated when the report
    changes to an importable state (APPROVED/PAYMENT_PROCESSING/PAID) via state change webhook.

    :param report_id: Report ID
    :param workspace: Workspace object
    :return: None
    """
    worker_logger = get_logger()
    worker_logger.info("Deleting accounting exports for report %s in workspace %s", report_id, workspace.id)

    expense_ids = Expense.objects.filter(
        workspace_id=workspace.id,
        report_id=report_id
    ).values_list('id', flat=True)

    if not expense_ids:
        worker_logger.info("No expenses found for report %s in workspace %s", report_id, workspace.id)
        return

    accounting_exports = AccountingExport.objects.filter(
        expenses__id__in=expense_ids,
        workspace_id=workspace.id,
        exported_at__isnull=True
    ).distinct()

    deleted_count = 0
    skipped_count = 0

    for accounting_export in accounting_exports:
        if accounting_export.status in ['ENQUEUED', 'IN_PROGRESS', 'EXPORT_QUEUED']:
            worker_logger.warning("Skipping deletion of accounting export %s - status is %s", accounting_export.id, accounting_export.status)
            skipped_count += 1
            continue

        worker_logger.info("Deleting accounting export %s for report %s", accounting_export.id, report_id)

        with transaction.atomic():
            delete_accounting_export_and_related_data(accounting_export, workspace.id)

        deleted_count += 1

    worker_logger.info("Completed deletion for report %s in workspace %s - deleted: %s, skipped: %s",
                report_id, workspace.id, deleted_count, skipped_count)


def _handle_expense_ejected_from_report(expense: Expense, expense_data: dict, workspace: Workspace) -> None:
    """
    Handle expense ejected from report
    :param expense: Expense object
    :param expense_data: Expense data from webhook
    :param workspace: Workspace object
    :return: None
    """
    worker_logger = get_logger()
    worker_logger.info("Handling expense %s ejected from report in workspace %s", expense.expense_id, workspace.id)

    accounting_export = AccountingExport.objects.filter(
        expenses=expense,
        workspace_id=workspace.id,
        exported_at__isnull=True
    ).first()

    if not accounting_export:
        worker_logger.info("No accounting export found for expense %s in workspace %s", expense.expense_id, workspace.id)
        return

    worker_logger.info("Removing expense %s from accounting export %s", expense.expense_id, accounting_export.id)

    if accounting_export.status in ['ENQUEUED', 'IN_PROGRESS', 'EXPORT_QUEUED']:
        worker_logger.warning("Cannot remove expense %s from export %s - status is %s", expense.expense_id, accounting_export.id, accounting_export.status)
        return

    with transaction.atomic():
        accounting_export.expenses.remove(expense)

        if not accounting_export.expenses.exists():
            worker_logger.info("Deleting empty accounting export %s after removing expense %s", accounting_export.id, expense.expense_id)
            delete_accounting_export_and_related_data(accounting_export, workspace.id)
        else:
            worker_logger.info("Accounting export %s still has expenses after removing %s", accounting_export.id, expense.expense_id)
