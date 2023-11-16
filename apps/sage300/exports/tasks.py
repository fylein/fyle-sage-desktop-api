from typing import List

from sage300.exports.purchase_invoice.tasks import PurchaseInvoice
from accounting_exports.models import AccountingExport

EXPORT_CLASS_MAP = {
    'PURCHACE_INVOICE': PurchaseInvoice,
}


def trigger_export_via_schedule(workspace_id: int, export_type: str, accounting_exports: List[AccountingExport]):
    """
    Trigger import via schedule
    :param workspace_id: Workspace id
    :param destination_field: Destination field
    :param source_field: Type of attribute (e.g., 'PROJECT', 'CATEGORY', 'COST_CENTER')
    """

    module_class = EXPORT_CLASS_MAP[export_type]
    item = module_class(workspace_id, accounting_exports)
    item.trigger_export()
