from django.db import models

from fyle_accounting_mappings.models import CategoryMapping, DestinationAttribute

from apps.sage300.exports.base_model import BaseExportModel
from apps.accounting_exports.models import AccountingExport
from apps.workspaces.models import AdvancedSetting
from apps.fyle.models import Expense, DependentFieldSetting


from sage_desktop_api.models.fields import (
    CustomDateTimeField,
    FloatNullField,
    StringNullField,
    TextNotNullField
)


class PurchaseInvoice(BaseExportModel):
    """
    Purchase Invoice Model
    """

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Accounting Export reference')
    accounting_date = CustomDateTimeField(help_text='accounting date of purchase invoice')
    amount = FloatNullField(help_text='Total Amount of the invoice')
    code = StringNullField(max_length=10, help_text='unique code for invoice')
    description = TextNotNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    tax_amount = FloatNullField(help_text='total tax amount of the invoice')
    vendor_id = StringNullField(help_text='id of vendor')

    class Meta:
        db_table = 'purchase_invoices'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_settings: AdvancedSetting = None):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """
        description = accounting_export.description

        vendor_id = self.get_vendor_id(accounting_export=accounting_export)
        amount = self.get_total_amount(accounting_export=accounting_export)
        invoice_date = self.get_invoice_date(accounting_export=accounting_export)

        purchase_invoice, _ = PurchaseInvoice.objects.update_or_create(
            accounting_export=accounting_export,
            defaults={
                'amount': amount,
                'vendor_id': vendor_id,
                'description': description,
                'invoice_date': invoice_date,
                'workspace_id': accounting_export.workspace_id
            }
        )

        return purchase_invoice


class PurchaseInvoiceLineitems(BaseExportModel):
    """
    Purchase Invoice Lineitem Model
    """

    accounts_payable_account_id = StringNullField(help_text='destination id of accounts payable account')
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, help_text='Reference to PurchaseInvoice')
    expense = models.OneToOneField(Expense, on_delete=models.PROTECT, help_text='Reference to Expense')
    amount = FloatNullField(help_text='Amount of the invoice')
    category_id = StringNullField(help_text='destination id of category')
    commitment_id = StringNullField(help_text='destination id of commitment')
    commitment_item_id = StringNullField(help_text='destination id of commitment item')
    cost_code_id = StringNullField(help_text='destination id of cost code')
    description = TextNotNullField(help_text='description for the invoice')
    job_id = StringNullField(help_text='destination id of job')
    tax_amount = FloatNullField(help_text='tax amount of the invoice')
    tax_group_id = StringNullField(help_text='destination id of tax group')
    standard_category_id = StringNullField(help_text='destination id of standard category')
    standard_cost_code_id = StringNullField(help_text='destination id of standard cost code')

    class Meta:
        db_table = 'purchase_invoice_lineitems'

    @classmethod
    def create_or_update_object(self, accounting_export: AccountingExport, advance_setting: AdvancedSetting):
        """
        Create Purchase Invoice
        :param accounting_export: expense group
        :return: purchase invoices object
        """

        expenses = accounting_export.expenses.all()
        purchase_invoice = PurchaseInvoice.objects.get(accounting_export=accounting_export)
        dependent_field_setting = DependentFieldSetting.objects.filter(workspace_id=accounting_export.workspace_id).first()

        cost_category_id = None
        cost_code_id = None

        purchase_invoice_lineitem_objects = []

        for lineitem in expenses:
            category = lineitem.category if (lineitem.category == lineitem.sub_category or lineitem.sub_category == None) else '{0} / {1}'.format(lineitem.category, lineitem.sub_category)

            account = CategoryMapping.objects.filter(
                source_category__value=category,
                workspace_id=accounting_export.workspace_id
            ).first()

            job_id = self.get_job_id(accounting_export, lineitem)
            standard_category_id = self.get_standard_category_id(accounting_export, lineitem)
            standard_cost_code_id = self.get_standard_cost_code_id(accounting_export, lineitem)
            description = self.get_expense_purpose(accounting_export.workspace_id, lineitem, lineitem.category, advance_setting)

            if dependent_field_setting:
                cost_code_id = self.get_cost_code_id(accounting_export, lineitem, dependent_field_setting, job_id)
                cost_category_id = self.get_cost_category_id(accounting_export, lineitem, dependent_field_setting, job_id, cost_code_id)

                if cost_code_id and cost_category_id:
                    commitment_item = DestinationAttribute.objects.filter(
                        attribute_type='COMMITMENT_ITEM',
                        workspace_id=accounting_export.workspace_id,
                        detail__contains={'cost_code_id': cost_code_id, 'category_id': cost_category_id}
                    ).first()

                    commitment_item_id = commitment_item.destination_id if commitment_item else None
                    commitment_id = commitment_item.detail['commitment_id'] if commitment_item else None

            purchase_invoice_lineitem_object, _ = PurchaseInvoiceLineitems.objects.update_or_create(
                purchase_invoice_id=purchase_invoice.id,
                expense_id=lineitem.id,
                defaults={
                    'amount': lineitem.amount,
                    'accounts_payable_account_id': account.destination_account.destination_id,
                    'job_id': job_id,
                    'commitment_id': commitment_id,
                    'commitment_item_id': commitment_item_id,
                    'standard_category_id': standard_category_id,
                    'standard_cost_code_id': standard_cost_code_id,
                    'category_id': cost_category_id,
                    'cost_code_id': cost_code_id,
                    'description': description,
                    'workspace_id': accounting_export.workspace_id
                }
            )
            purchase_invoice_lineitem_objects.append(purchase_invoice_lineitem_object)

        return purchase_invoice_lineitem_objects
