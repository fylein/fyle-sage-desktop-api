from django.db import models

from fyle_accounting_mappings.models import CategoryMapping

from apps.sage300.exports.base_model import BaseExportModel
from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense, DependentFieldSetting
from apps.workspaces.models import AdvancedSetting

from sage_desktop_api.models.fields import (
    CustomDateTimeField,
    FloatNullField,
    StringNullField,
    TextNotNullField
)


class DirectCost(BaseExportModel):
    """
    Direct Cost Model
    """

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')
    accounting_date = CustomDateTimeField(help_text='accounting date of direct cost')
    code = StringNullField(max_length=10, help_text='unique code for invoice')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    category_id = StringNullField(help_text='destination id of category')
    commitment_id = StringNullField(help_text='destination id of commitment')
    cost_code_id = StringNullField(help_text='destination id of cost code')
    credit_card_account_id = StringNullField(help_text='destination id of credit card account')
    debit_card_account_id = StringNullField(help_text='destination id of debit card account')
    description = TextNotNullField(help_text='description for the invoice')
    job_id = StringNullField(help_text='destination id of job')
    standard_category_id = StringNullField(help_text='destination id of standard category')
    standard_cost_code_id = StringNullField(help_text='destination id of standard cost code')

    class Meta:
        db_table = 'direct_costs'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Direct Cost
        :param accounting_export: expense group
        :return: Direct cost object
        """

        expense = accounting_export.expenses.first()
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

        cost_category_id = None
        cost_code_id = None

        account = CategoryMapping.objects.filter(
            source_category__value=expense.category,
            workspace_id=accounting_export.workspace_id
        ).first()

        job_id = self.get_job_id(accounting_export, expense)
        commitment_id = self.get_commitment_id(accounting_export, expense)
        standard_category_id = self.get_standard_category_id(accounting_export, expense)
        standard_cost_code_id = self.get_standard_cost_code_id(accounting_export, expense)
        description = self.get_expense_purpose(accounting_export.workspace_id, expense, expense.category, advance_setting)

        if dependent_field_setting:
            cost_code_id = self.get_cost_code_id(accounting_export, expense, dependent_field_setting, job_id)
            cost_category_id = self.get_cost_category_id(accounting_export, expense, dependent_field_setting, job_id, cost_code_id)

        direct_cost_object, _ = DirectCost.objects.update_or_create(
            expense_id=expense.id,
            accounting_export=accounting_export,
            defaults={
                'amount': expense.amount,
                'credit_card_account_id': account.destination_account.destination_id,
                'job_id': job_id,
                'commitment_id': commitment_id,
                'standard_category_id': standard_category_id,
                'standard_cost_code_id': standard_cost_code_id,
                'category_id': cost_category_id,
                'cost_code_id': cost_code_id,
                'description': description,
                'workspace_id': accounting_export.workspace_id
            }
        )

        return direct_cost_object
