import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from django_q.tasks import async_task

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum

from apps.workspaces.models import ExportSetting
from apps.workspaces.helpers import clear_workspace_errors_on_export_type_change
from apps.sage300.actions import update_accounting_export_summary
from apps.accounting_exports.models import AccountingExportSummary


logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=ExportSetting)
def run_pre_save_export_settings_triggers(sender: type[ExportSetting], instance: ExportSetting, **kwargs) -> None:
    """
    Run pre save export setting triggers
    """
    existing_export_settings = ExportSetting.objects.filter(
        workspace_id=instance.workspace_id
    ).first()

    if existing_export_settings:
        instance._pre_save_old_export_settings = {
            'reimbursable_expenses_export_type': existing_export_settings.reimbursable_expenses_export_type,
            'credit_card_expense_export_type': existing_export_settings.credit_card_expense_export_type,
        }
        # TODO: move these async_tasks to utility worker later
        is_reimbursable_state_changed = (
            existing_export_settings.reimbursable_expense_state != instance.reimbursable_expense_state
        )
        is_paid_to_processing = (
            existing_export_settings.reimbursable_expense_state == ExpenseStateEnum.PAID
            and instance.reimbursable_expense_state == ExpenseStateEnum.PAYMENT_PROCESSING
        )
        if existing_export_settings.reimbursable_expenses_export_type and is_reimbursable_state_changed and is_paid_to_processing:
            logger.info(f'Reimbursable expense state changed from {existing_export_settings.reimbursable_expense_state} to {instance.reimbursable_expense_state} for workspace {instance.workspace_id}, so pulling the data from Fyle')
            async_task('apps.fyle.tasks.import_expenses', workspace_id=instance.workspace_id, source_account_type='PERSONAL_CASH_ACCOUNT', fund_source_key='PERSONAL', imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE)

        is_ccc_state_changed = (
            existing_export_settings.credit_card_expense_state != instance.credit_card_expense_state
        )
        is_paid_to_approved = (
            existing_export_settings.credit_card_expense_state == ExpenseStateEnum.PAID
            and instance.credit_card_expense_state == ExpenseStateEnum.APPROVED
        )
        if existing_export_settings.credit_card_expense_export_type and is_ccc_state_changed and is_paid_to_approved:
            logger.info(f'Corporate credit card expense state changed from {existing_export_settings.credit_card_expense_state} to {instance.credit_card_expense_state} for workspace {instance.workspace_id}, so pulling the data from Fyle')
            async_task('apps.fyle.tasks.import_expenses', workspace_id=instance.workspace_id, source_account_type='PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT', fund_source_key='CCC', imported_from=ExpenseImportSourceEnum.CONFIGURATION_UPDATE)
    else:
        instance._pre_save_old_export_settings = {
            'reimbursable_expenses_export_type': None,
            'credit_card_expense_export_type': None,
        }


@receiver(post_save, sender=ExportSetting)
def run_post_save_export_settings_triggers(sender: type[ExportSetting], instance: ExportSetting, created: bool, **kwargs) -> None:
    """
    Run post save export setting triggers to clear errors when export types change
    """
    if hasattr(instance, '_pre_save_old_export_settings'):
        old_export_settings = instance._pre_save_old_export_settings
        delattr(instance, '_pre_save_old_export_settings')
    else:
        old_export_settings = {
            'reimbursable_expenses_export_type': None,
            'credit_card_expense_export_type': None,
        }

    clear_workspace_errors_on_export_type_change(
        workspace_id=instance.workspace_id,
        old_export_settings=old_export_settings,
        new_export_settings=instance
    )

    last_export_detail = AccountingExportSummary.objects.filter(workspace_id=instance.workspace_id).first()
    if last_export_detail and last_export_detail.last_exported_at:
        update_accounting_export_summary(instance.workspace_id)
