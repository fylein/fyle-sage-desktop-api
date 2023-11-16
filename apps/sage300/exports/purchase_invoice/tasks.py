from datetime import datetime
from django.db import transaction

from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.models import PurchaceInvoice, PurchaceInvoiceLineitems
from apps.workspaces.models import ExportSetting
from apps.sage300.utils import SageDesktopConnector


class ExportPurchaceInvoice:

    """
    Class for purchace invoice module
    """

    def __init__(
        self,
        workspace_id: int,
    ):
        self.workspace_id = workspace_id

    def trigger_import(self):
        """
        Trigger import for Project module
        """
        self.check_accounting_export_and_start_import()

    def __construct_purchace_invoice(item, lineitem):
        pass

    def post_purchace_invoice(self, item, lineitem):
        """
        Export Purchace Invoice
        """

        try:
            purchace_invoice_payload = self.__construct_purchace_invoice(item, lineitem)

            sage300_connection = SageDesktopConnector()
            created_purchace_invoice_ = sage300_connection.connection.documents.post_document(purchace_invoice_payload)
            return created_purchace_invoice_

        except Exception as e:
            print(e)

    def create_purchace_invoice(self, accounting_export: AccountingExport):
        """
        function to create purchace invoice
        """

        export_settings = ExportSetting.objects.filter(workspace_id=accounting_export.workspace_id)

        if accounting_export.status not in ['IN_PROGRESS', 'COMPLETE']:
            accounting_export.status = 'IN_PROGRESS'
            accounting_export.save()
        else:
            return

        try:
            with transaction.atomic():
                purchace_invoice_object = PurchaceInvoice.create_expense_report(accounting_export)

                purchace_invoice_lineitems_objects = PurchaceInvoiceLineitems.create_expense_report_lineitems(
                    accounting_export, export_settings
                )

                created_purchace_invoice = self.post_purchace_invoice(
                    purchace_invoice_object, purchace_invoice_lineitems_objects
                )

                accounting_export.detail = created_purchace_invoice
                accounting_export.status = 'COMPLETE'
                accounting_export.exported_at = datetime.now()

                accounting_export.save()

        except Exception as e:
            print(e)
            # will add execptions here
