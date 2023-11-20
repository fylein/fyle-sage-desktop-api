from datetime import datetime
from django.db import transaction

from apps.sage300.exports.tasks import AccountingDataExporter
from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.workspaces.models import ExportSetting
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
