from datetime import datetime
from django.db import transaction

from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import
from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.workspaces.models import ExportSetting
from apps.sage300.utils import SageDesktopConnector


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

        purchase_invoice_payload = self.__construct_purchase_invoice(item, lineitem)

        sage300_connection = SageDesktopConnector()
        created_purchase_invoice = sage300_connection.connection.documents.post_document(purchase_invoice_payload)
        return created_purchase_invoice

    def create_purchase_invoice(self, accounting_export: AccountingExport):
        """
        function to create purchase invoice
        """

        export_settings = ExportSetting.objects.filter(workspace_id=accounting_export.workspace_id)

        if accounting_export.status not in ['IN_PROGRESS', 'COMPLETE']:
            accounting_export.status = 'IN_PROGRESS'
            accounting_export.save()
        else:
            return

        try:
            with transaction.atomic():
                purchase_invoice_object = PurchaseInvoice.create_expense_report(accounting_export)

                purchase_invoice_lineitems_objects = PurchaseInvoiceLineitems.create_expense_report_lineitems(
                    accounting_export, export_settings
                )

                created_purchase_invoice = self.post_purchase_invoice(
                    purchase_invoice_object, purchase_invoice_lineitems_objects
                )

                accounting_export.detail = created_purchase_invoice
                accounting_export.status = 'COMPLETE'
                accounting_export.exported_at = datetime.now()

                accounting_export.save()

        except Exception as e:
            print(e)
            # will add execptions here


def create_purchase_invoice(accounting_export: AccountingExport):
    """
    Helper function to create and export a purchase invoice.
    """
    export_purchase_invoice_instance = ExportPurchaseInvoice()

    # Create and export the purchase invoice using the base class method
    exported_purchase_invoice = export_purchase_invoice_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_purchase_invoice
