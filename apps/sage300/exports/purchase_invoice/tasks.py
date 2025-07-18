import logging
from typing import Dict, List

from fyle_accounting_library.fyle_platform.enums import ExpenseImportSourceEnum

from apps.accounting_exports.models import AccountingExport
from apps.sage300.exceptions import handle_sage300_exceptions
from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.sage300.exports.purchase_invoice.models import PurchaseInvoice, PurchaseInvoiceLineitems
from apps.sage300.exports.purchase_invoice.queues import check_accounting_export_and_start_import
from apps.sage300.utils import SageDesktopConnector
from apps.workspaces.models import ImportSetting, Sage300Credential

logger = logging.getLogger(__name__)
logger.level = logging.INFO

DOCUMENT_TYPE_ID = '76744AB9-4697-430A-ADB5-701E633472A9'


class ExportPurchaseInvoice(AccountingDataExporter):
    """
    Class for handling the export of purchase invoices to Sage 300.
    Extends the base AccountingDataExporter class.
    """

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = PurchaseInvoice
        self.lineitem_model = PurchaseInvoiceLineitems

    def trigger_export(self, workspace_id, accounting_export_ids, is_auto_export, interval_hours, triggered_by: ExpenseImportSourceEnum, run_in_rabbitmq_worker: bool = False):
        """
        Trigger the import process for the Project module.
        """
        check_accounting_export_and_start_import(workspace_id=workspace_id, accounting_export_ids=accounting_export_ids, is_auto_export=is_auto_export, interval_hours=interval_hours, triggered_by=triggered_by, run_in_rabbitmq_worker=run_in_rabbitmq_worker)

    def __construct_purchase_invoice(self, body: PurchaseInvoice, lineitems: List[PurchaseInvoiceLineitems]) -> Dict:
        """
        Construct the payload for the purchase invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """

        import_settings = ImportSetting.objects.filter(workspace_id=body.workspace_id).first()

        purchase_invoice_lineitem_payload = []
        for lineitem in lineitems:
            expense = {
                "AccountsPayableAccountId": lineitem.accounts_payable_id,
                "Amount": lineitem.amount,
                "CategoryId": lineitem.category_id,
                "CostCodeId": lineitem.cost_code_id,
                "Description": lineitem.description[0:30],
                "ExpenseAccountId": lineitem.expense_account_id,
                "JobId": lineitem.job_id,
                "StandardCategoryId": lineitem.standard_category_id,
                "StandardCostCodeId": lineitem.standard_cost_code_id
            }

            if import_settings.add_commitment_details:
                expense['CommitmentId'] = lineitem.commitment_id
                expense['CommitmentItemId'] = lineitem.commitment_item_id

            purchase_invoice_lineitem_payload.append(expense)

        purchase_invoice_payload = {
            'DocumentTypeId': DOCUMENT_TYPE_ID,
            'Snapshot': {
                'Distributions': purchase_invoice_lineitem_payload,
                'Header': {
                    'AccountingDate': body.invoice_date,
                    'Amount': body.amount,
                    "Code": '{}-{}'.format(body.description['fund_source'], body.id),
                    "Description": body.description['employee_email'],
                    "InvoiceDate": body.invoice_date,
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
        sage300_credentials = Sage300Credential.get_active_sage300_credentials(accounting_export.workspace_id)
        # Establish a connection to Sage 300
        sage300_connection = SageDesktopConnector(sage300_credentials, accounting_export.workspace_id)

        # Post the purchase invoice to Sage 300
        logger.info('purchase invoice payload %s for workspace_id %s', purchase_invoice_payload, accounting_export.workspace_id)

        created_purchase_invoice_id = sage300_connection.connection.documents.post_document(purchase_invoice_payload)
        accounting_export.export_id = created_purchase_invoice_id
        accounting_export.save()

        exported_purchase_invoice_id = sage300_connection.connection.documents.export_document(created_purchase_invoice_id)

        return exported_purchase_invoice_id


@handle_sage300_exceptions()
def create_purchase_invoice(accounting_export_id: int, _: bool):
    """
    Helper function to create and export a purchase invoice.
    """
    accounting_export: AccountingExport = AccountingExport.objects.get(id=accounting_export_id)
    export_purchase_invoice_instance = ExportPurchaseInvoice()

    # Create and export the purchase invoice using the base class method
    exported_purchase_invoice = export_purchase_invoice_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_purchase_invoice
