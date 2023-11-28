from typing import Dict, List

from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector
from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.sage300.exceptions import handle_sage300_exceptions


class ExportPurchaseInvoice(AccountingDataExporter):
    """
    Class for handling the export of purchase invoices to Sage 300.
    Extends the base AccountingDataExporter class.
    """

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = PurchaseInvoice
        self.lineitem_model = PurchaseInvoiceLineitems

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger the import process for the Project module.
        """
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_purchase_invoice(self, body: PurchaseInvoice, lineitems: List[PurchaseInvoiceLineitems]) -> Dict:
        """
        Construct the payload for the purchase invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """

        purchase_invoice_lineitem_payload = []
        for lineitem in lineitems:
            expense = {
                "AccountsPayableAccountId": lineitem.accounts_payable_account_id,
                "Amount": lineitem.amount,
                "CategoryId": lineitem.category_id,
                "CostCodeId": lineitem.cost_code_id,
                "Description": 'sample description',
                "ExpenseAccountId": lineitem.accounts_payable_account_id,
                "JobId": lineitem.job_id,
                "StandardCategoryId": lineitem.standard_category_id,
                "StandardCostCodeId": lineitem.standard_cost_code_id
            }

            purchase_invoice_lineitem_payload.append(expense)

        transaction_date = '2023-08-17'
        purchase_invoice_payload = {
            'DocumentTypeId': '76744AB9-4697-430A-ADB5-701E633472A9',
            'Snapshot': {
                'Distributions': purchase_invoice_lineitem_payload,
                'Header': {
                    'AccountingDate': transaction_date,
                    'Amount': body.amount,
                    "Code": 'hello',
                    "Description": 'sample description',
                    "InvoiceDate": transaction_date,
                    "VendorId": body.vendor_id
                }
            }
        }

        return purchase_invoice_payload

    def post(self, accounting_export, item, lineitem):
        """
        Export the purchase invoice to Sage 300.
        """

        purchase_invoice_payload = self.__construct_purchase_invoice(item, lineitem)
        sage300_credentials = Sage300Credential.objects.filter(workspace_id=accounting_export.workspace_id).first()
        # Establish a connection to Sage 300
        sage300_connection = SageDesktopConnector(sage300_credentials, accounting_export.workspace_id)

        # Post the purchase invoice to Sage 300
        created_purchase_invoice_id = sage300_connection.connection.documents.post_document(purchase_invoice_payload)

        print('createds sdoijsodif', created_purchase_invoice_id)
        accounting_export.export_id = created_purchase_invoice_id
        accounting_export.save()

        exported_purchase_invoice_id = sage300_connection.connection.documents.export_document(created_purchase_invoice_id)

        return exported_purchase_invoice_id


@handle_sage300_exceptions()
def create_purchase_invoice(accounting_export: AccountingExport):
    """
    Helper function to create and export a purchase invoice.
    """
    export_purchase_invoice_instance = ExportPurchaseInvoice()

    # Create and export the purchase invoice using the base class method
    exported_purchase_invoice = export_purchase_invoice_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_purchase_invoice
