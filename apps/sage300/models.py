from django.db import models
from apps.workspaces.models import BaseModel
from sage_desktop_api.models.fields import (
    StringNotNullField,
    CustomDateTimeField,
    FloatNullField,
    IntegerNullField,
    TextNotNullField
)
from apps.accounting_exports.models import AccountingExport


class Invoice(BaseModel):
    """
    Invoice Table Model Class

    Example Data ->
    amount: 12.31,
    date: '2021-04-26',
    accounting_date: 'Accounts Payable',
    description: 'Reimbursable Expenses by Shwetabh',
    tax_amount: 1.32,
    vendor_id: '12312123123'
    """

    id = models.AutoField(primary_key=True)
    amount = FloatNullField(help_text='Invoice amount')
    accounting_date = StringNotNullField(help_text='Accounting date')
    description = TextNotNullField(help_text='Invoice description')
    tax_amount = FloatNullField(help_text='Tax amount')
    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Reference to AccountingExport model')
    vendor_id = StringNotNullField(help_text='Vendor ID')
    code = StringNotNullField(max_length=15, help_text="unique key for each document")

    class Meta:
        db_table = 'invoice'


class InvoiceLineitems(BaseModel):
    """
    Invoice Table Model Class

    Example Data ->
    amount: 12.31,
    accounts_payable_account_id: '123123',
    expense_account_id: '1231231',
    description: 'Reimbursable Expenses by Shwetabh',
    job_id: '123123',
    cost_code_id: '12312123123'
    category_id: '123'
    """

    id = models.AutoField(primary_key=True)
    amount = FloatNullField(help_text='Invoice lineitem amount')
    accounts_payable_account_id = StringNotNullField(help_text='Accounts Payable Account Id')
    description = TextNotNullField(help_text='Invoice lineitem description')
    expense_account_id = StringNotNullField(help_text='Expense Account Id')
    job_id = StringNotNullField(help_text='Job Id')
    cost_code_id = StringNotNullField(help_text='Cost Code Id')
    category_id = StringNotNullField(help_text='Category Id')
    invoice_id = models.ForeignKey(Invoice, on_delete=models.PROTECT, help_text='Reference to Invoice model')

    class Meta:
        db_table = 'invoice_lineitems'


class DirectCost(BaseModel):
    """
    Invoice Table Model Class

    Example Data ->
    amount: 12.31,
    accounts_payable_account_id: '123123',
    expense_account_id: '1231231',
    description: 'Reimbursable Expenses by Shwetabh',
    job_id: '123123',
    cost_code_id: '12312123123'
    category_id: '123'
    """

    id = models.AutoField(primary_key=True)
    amount = FloatNullField(help_text='Invoice amount')
    code = StringNotNullField(help_text='Code Id')
    job_id = StringNotNullField(help_text='Job Id')
    cost_code_id = StringNotNullField(help_text='Cost Code Id')
    category_id = StringNotNullField(help_text='Category Id')
    accounting_export = models.OneToOneField(AccountingExport, on_delete=models.PROTECT, help_text='Reference to AccountingExport model')
    credit_card_account_id = StringNotNullField(help_text='Credit Card Account Id')
    debit_card_account_id = StringNotNullField(help_text='Debit Card Account Id')
    transaction_date = CustomDateTimeField(help_text='Transaction Date')
    description = TextNotNullField(help_text='Direct Costs description')
    transaction_type = IntegerNullField(help_text='Transaction Type')

    class Meta:
        db_table = 'direct_cost'
