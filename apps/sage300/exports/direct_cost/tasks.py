from typing import Dict

from apps.sage300.exports.accounting_export import AccountingDataExporter
from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import Sage300Credential
from apps.sage300.utils import SageDesktopConnector
from apps.sage300.exports.direct_cost.queues import check_accounting_export_and_start_import
from apps.sage300.exceptions import handle_sage300_exceptions
from apps.sage300.exports.direct_cost.models import DirectCost


class ExportDirectCost(AccountingDataExporter):
    """
    Class for handling the export of Direct Cost to Sage 300.
    Extends the base AccountingDataExporter class.
    """

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.body_model = DirectCost

    def trigger_export(self, workspace_id, accounting_export_ids):
        """
        Trigger the import process for the Project module.
        """
        print('i am here direct')
        check_accounting_export_and_start_import(workspace_id, accounting_export_ids)

    def __construct_direct_cost(self, body: DirectCost) -> Dict:
        """
        Construct the payload for the direct invoice.
        :param expense_report: ExpenseReport object extracted from database
        :param expense_report_lineitems: ExpenseReportLineitem objects extracted from database
        :return: constructed expense_report
        """

        transaction_date = '2023-08-17'
        direct_cost_payload = {
            "AccountingDate": "2023-11-17",
            "Amount": 120,
            "Code": 234234,
            "CategoryId": "ece00064-b585-4f87-b0bc-b06100a9bec8",
            "CostCodeId": "d3b321be-1e6c-4d4b-add4-b06100a9bd2c",
            "CreditAccountId": "b8524a2e-5aef-435f-8823-b05b00f3c52f",
            "DebitAccountId": "5aa3ee7f-9c0d-42a6-86bf-b05b00f3c9dd",
            "Description": "Fyle - Line 1 Wow",
            "JobId": "5e0eb476-b189-4409-b9b3-b061009602a4",
            "TransactionDate": transaction_date,
            "StandardCategoryId": "302918fb-2f89-4d7f-972a-b05b00f3c431",
            "TransactionType": 1
        }

        return direct_cost_payload

    def post(self, accounting_export, item, lineitem = None):
        """
        Export the direct cost to Sage 300.
        """

        direct_cost_payload = self.__construct_direct_cost(item)
        sage300_credentials = Sage300Credential.objects.filter(workspace_id=accounting_export.workspace_id).first()
        # Establish a connection to Sage 300
        sage300_connection = SageDesktopConnector(sage300_credentials, accounting_export.workspace_id)

        # Post the direct cost to Sage 300
        created_direct_cost_export_id = sage300_connection.connection.direct_costs.post_direct_cost(direct_cost_payload)

        accounting_export.export_id = created_direct_cost_export_id
        accounting_export.save()

        # exported_purchase_invoice_id = sage300_connection.connection.documents.export_document(direct_cost_payload)

        return created_direct_cost_export_id


@handle_sage300_exceptions()
def create_direct_cost(accounting_export: AccountingExport):
    """
    Helper function to create and export a direct cost.
    """
    export_direct_cost_instance = ExportDirectCost()

    # Create and export the direct cost using the base class method
    exported_direct_cost = export_direct_cost_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_direct_cost
