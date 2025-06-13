import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from django_q.tasks import async_task

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum, ExpenseStateEnum

from apps.workspaces.models import ExportSetting


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
