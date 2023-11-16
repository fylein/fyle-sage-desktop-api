from django.db import models

from apps.sage300.exports.base_model import BaseExportModel
from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import Expense


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

    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Expense group reference')
    accounting_date = CustomDateTimeField(help_text='accounting date of purchase invoice')
    amount = FloatNullField(help_text='Total Amount of the invoice')
    code = StringNullField(max_length=10, help_text='unique code for invoice')
    description = TextNotNullField(help_text='description for the invoice')
    invoice_date = CustomDateTimeField(help_text='date of invoice')
    tax_amount = FloatNullField(help_text='total tax amount of the invoice')
    vendor_id = StringNullField(help_text='id of vendor')

    class Meta:
        db_table = 'purchase_invoices'


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
    cost_code_id = StringNullField(help_text='destination id of cost code')
    description = TextNotNullField(help_text='description for the invoice')
    job_id = StringNullField(help_text='destination id of job')
    tax_amount = FloatNullField(help_text='tax amount of the invoice')
    tax_group_id = StringNullField(help_text='destination id of tax group')
    standard_category_id = StringNullField(help_text='destination id of standard category')
    standard_cost_code_id = StringNullField(help_text='destination id of standard cost code')

    class Meta:
        db_table = 'purchase_invoice_lineitems'
