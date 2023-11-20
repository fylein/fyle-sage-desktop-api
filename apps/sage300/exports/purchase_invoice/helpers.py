from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.tasks import ExportPurchaseInvoice


def create_purchase_invoice(accounting_export: AccountingExport):
    """
    Helper function to create purchase invoice
    """

    export_purchase_invoice_instance = ExportPurchaseInvoice()
    exported_purchase_invoice = export_purchase_invoice_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_purchase_invoice
