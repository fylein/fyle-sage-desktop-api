from datetime import datetime
from django.db import models

from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense
from apps.workspaces.models import Workspace, FyleCredential, AdvancedSetting


class BaseExportModel(models.Model):
    """
    Base Model for Sage300 Export
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    def get_expense_purpose(workspace_id, lineitem: Expense, category: str, advance_setting: AdvancedSetting) -> str:
        workspace = Workspace.objects.get(id=workspace_id)
        org_id = workspace.org_id

        fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
        cluster_domain = fyle_credentials.cluster_domain
        workspace.cluster_domain = cluster_domain
        workspace.save()

        expense_link = '{0}/app/main/#/enterprise/view_expense/{1}?org_id={2}'.format(
            cluster_domain, lineitem.expense_id, org_id
        )

        memo_structure = advance_setting.expense_memo_structure

        details = {
            'employee_email': lineitem.employee_email,
            'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
            'category': '{0}'.format(category) if lineitem.category else '',
            'purpose': '{0}'.format(lineitem.purpose) if lineitem.purpose else '',
            'report_number': '{0}'.format(lineitem.claim_number),
            'spent_on': '{0}'.format(lineitem.spent_at.date()) if lineitem.spent_at else '',
            'expense_link': expense_link
        }

        purpose = ''

        for id, field in enumerate(memo_structure):
            if field in details:
                purpose += details[field]
                if id + 1 != len(memo_structure):
                    purpose = '{0} - '.format(purpose)

        return purpose

    def get_vendor_id(accounting_export: AccountingExport):
        return '124'

    def get_total_amount(accounting_export: AccountingExport):
        return '123123'

    def get_invoice_date(accounting_export: AccountingExport):
        return datetime.now()

    def get_job_id(accounting_export: AccountingExport, expense: Expense):
        return '2312'

    def get_commitment_id(accounting_export: AccountingExport, expense: Expense):
        return '12312'

    def get_standard_category_id(accounting_export: AccountingExport, expense: Expense):
        return '123123'

    def get_standard_cost_code_id(accounting_export: AccountingExport, expense: Expense):
        return '123123'
    class Meta:
        abstract = True
