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
            "AccountingDate": transaction_date,
            "Amount": body.amount,
            "Code": 234234,
            "CategoryId": body.category_id,
            "CostCodeId": body.cost_code_id,
            "CreditAccountId": body.credit_card_account_id,
            "DebitAccountId": body.debit_card_account_id,
            "Description": "Fyle - Line 1 Wow",
            "JobId": body.job_id,
            "TransactionDate": transaction_date,
            "StandardCategoryId": body.standard_category_id,
            "StandardCostCodeId": body.standard_cost_code_id,
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

        exported_direct_cost_id = sage300_connection.connection.direct_costs.export_direct_cost(created_direct_cost_export_id)

        return exported_direct_cost_id


@handle_sage300_exceptions()
def create_direct_cost(accounting_export: AccountingExport):
    """
    Helper function to create and export a direct cost.
    """
    export_direct_cost_instance = ExportDirectCost()

    # Create and export the direct cost using the base class method
    exported_direct_cost = export_direct_cost_instance.create_sage300_object(accounting_export=accounting_export)

    return exported_direct_cost
