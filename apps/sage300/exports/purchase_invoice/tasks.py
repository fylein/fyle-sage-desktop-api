from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.accounting_exports.models import AccountingExport
from apps.sage300.utils import SageDesktopConnector
from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import


class ExportPurchaseInvoice(AccountingDataExporter):
    """
    Class for handling the export of purchase invoices to Sage 300.
    Extends the base AccountingDataExporter class.
    """

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger the import process for the Project module.
        """
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_purchase_invoice(self, item, lineitem):
        """
        Construct the payload for the purchase invoice.
        """
        # Implementation for constructing the purchase invoice payload goes here
        pass

    def post(self, item, lineitem):
        """
        Export the purchase invoice to Sage 300.
        """
        try:
            purchase_invoice_payload = self.__construct_purchase_invoice(item, lineitem)

            # Establish a connection to Sage 300
            sage300_connection = SageDesktopConnector()

            # Post the purchase invoice to Sage 300
            created_purchase_invoice = sage300_connection.connection.documents.post_document(purchase_invoice_payload)
            return created_purchase_invoice

        except Exception as e:
            print(e)


def create_purchase_invoice(accounting_export: AccountingExport):
    """
    Helper function to create and export a purchase invoice.
    """
    export_purchase_invoice_instance = ExportPurchaseInvoice()

    # Create and export the purchase invoice using the base class method
    exported_purchase_invoice = export_purchase_invoice_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_purchase_invoice
