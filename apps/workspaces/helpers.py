from typing import List
from django.db import transaction

from apps.accounting_exports.models import AccountingExport, Error
from apps.workspaces.models import ExportSetting
import logging

logger = logging.getLogger(__name__)


def get_error_model_path() -> str:
    """
    Get error model path: This is for imports submodule
    :return: str
    """
    return 'apps.accounting_exports.models.Error'


def get_import_configuration_model_path() -> str:
    """
    Get import configuration model path: This is for imports submodule
    :return: str
    """
    return 'apps.workspaces.models.ImportSetting'


def get_cost_code_update_method_path() -> str:
    """
    Update and disable cost code path
    :return: str
    """
    return 'apps.sage300.dependent_fields.update_and_disable_cost_code'


def get_app_name() -> str:
    """
    Get app name
    :return: str
    """
    return 'SAGE300'


def clear_workspace_errors_on_export_type_change(
    workspace_id: int,
    old_export_settings: dict,
    new_export_settings: ExportSetting
) -> None:
    """
    Clear workspace errors when export type settings change.
    This function clears errors and resets accounting exports when the export type
    for reimbursable or corporate credit card expenses changes. It ensures that
    previously failed exports can be re-attempted with the new configuration.

    Args:
        workspace_id: The workspace ID to clear errors for
        old_export_settings: Previous export settings as dictionary
        new_export_settings: New ExportSetting model instance
    """
    try:
        with transaction.atomic():
            old_reimburse = old_export_settings.get('reimbursable_expenses_export_type')
            new_reimburse = new_export_settings.reimbursable_expenses_export_type
            old_ccc = old_export_settings.get('credit_card_expense_export_type')
            new_ccc = new_export_settings.credit_card_expense_export_type

            reimburse_changed = old_reimburse != new_reimburse
            ccc_changed = old_ccc != new_ccc

            if reimburse_changed:
                logger.info("Reimbursable export type changed from '%s' to '%s' in workspace %s", old_reimburse, new_reimburse, workspace_id)
            if ccc_changed:
                logger.info("CCC export type changed from '%s' to '%s' in workspace %s", old_ccc, new_ccc, workspace_id)

            affected_fund_sources: List[str] = []
            if reimburse_changed:
                affected_fund_sources.append('PERSONAL')
            if ccc_changed:
                affected_fund_sources.append('CCC')

            total_deleted_errors = 0

            if affected_fund_sources:
                logger.info("Export type changed for fund sources %s in workspace %s", affected_fund_sources, workspace_id)

                affected_accounting_exports = AccountingExport.objects.select_for_update().filter(
                    workspace_id=workspace_id,
                    exported_at__isnull=True,
                    status__in=['FAILED', 'FATAL', 'EXPORT_QUEUED'],
                    fund_source__in=affected_fund_sources
                )

                affected_accounting_export_ids = list(affected_accounting_exports.values_list('id', flat=True))

                if affected_accounting_export_ids:
                    logger.info("Found %s affected accounting exports", len(affected_accounting_export_ids))

                    # Clear direct errors for affected accounting exports
                    accounting_export_errors = Error.objects.filter(
                        workspace_id=workspace_id,
                        accounting_export_id__in=affected_accounting_export_ids
                    )
                    if accounting_export_errors.exists():
                        deleted_direct_errors_count, _ = accounting_export_errors.delete()
                        total_deleted_errors += deleted_direct_errors_count
                        logger.info("Cleared %s direct accounting export errors", deleted_direct_errors_count)

                    all_mapping_errors = Error.objects.filter(
                        workspace_id=workspace_id,
                        type__in=['EMPLOYEE_MAPPING', 'CATEGORY_MAPPING'],
                        is_resolved=False
                    )
                    if all_mapping_errors.exists():
                        deleted_mapping_errors_count, _ = all_mapping_errors.delete()
                        total_deleted_errors += deleted_mapping_errors_count
                        logger.info("Cleared %s mapping errors (all EMPLOYEE_MAPPING and CATEGORY_MAPPING errors)", deleted_mapping_errors_count)

                    updated_exports = affected_accounting_exports.filter(
                        status__in=['FAILED', 'FATAL', 'EXPORT_QUEUED']
                    ).update(status='EXPORT_READY', sage300_errors=None, detail=None, mapping_errors=None)

                    if updated_exports > 0:
                        logger.info("Reset %s accounting exports to EXPORT_READY status", updated_exports)

            logger.info("Successfully cleared %s errors for workspace %s", total_deleted_errors, workspace_id)

    except Exception as e:
        logger.error("Error clearing workspace errors for workspace %s: %s", workspace_id, str(e))
        raise
