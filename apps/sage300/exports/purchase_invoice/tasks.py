from apps.sage300.exports.tasks import AccountingDataExporter
from apps.sage300.utils import SageDesktopConnector


class ExportPurchaseInvoice(AccountingDataExporter):

    """
    Class for purchase invoice module
    """

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger import for Project module
        """
        from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_purchase_invoice(item, lineitem):
        pass

    def post(self, item, lineitem):
        """
        Export Purchase Invoice
        """

        try:
            purchase_invoice_payload = self.__construct_purchase_invoice(item, lineitem)

            sage300_connection = SageDesktopConnector()
            created_purchase_invoice = sage300_connection.connection.documents.post_document(purchase_invoice_payload)
            return created_purchase_invoice

        except Exception as e:
            print(e)
