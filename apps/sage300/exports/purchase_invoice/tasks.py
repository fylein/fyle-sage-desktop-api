from datetime import datetime
from django.db import transaction

from apps.accounting_exports.models import AccountingExport
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.workspaces.models import AdvancedSetting
from apps.sage300.utils import SageDesktopConnector # noqa


class ExportPurchaseInvoice:

    """
    Class for purchase invoice module
    """

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger import for Project module
        """
        from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_purchase_invoice(self, item, lineitem):
        return 'wow'

    def post_purchase_invoice(self, item, lineitem):
        """
        Export Purchase Invoice
        """

        try:
            # purchase_invoice_payload = self.__construct_purchase_invoice(item, lineitem)

            # sage300_connection = SageDesktopConnector()
            # created_purchase_invoice_ = sage300_connection.connection.documents.post_document(purchase_invoice_payload)
            return 'completed'

        except Exception as e:
            print(e)

    def create_purchase_invoice(self, accounting_export: AccountingExport):
        """
        function to create purchase invoice
        """
        advance_setting = AdvancedSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

        if accounting_export.status not in ['IN_PROGRESS', 'COMPLETE']:
            accounting_export.status = 'IN_PROGRESS'
            accounting_export.save()
        else:
            return
        try:
            with transaction.atomic():
                purchase_invoice_object = PurchaseInvoice.create_purchase_invoice(accounting_export=accounting_export)

                purchase_invoice_lineitems_objects = PurchaseInvoiceLineitems.create_purchase_invoice_lineitems(
                    accounting_export, advance_setting
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
