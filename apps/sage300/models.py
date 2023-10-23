from django.db import models
from apps.workspaces.models import BaseModel
from sage_desktop_api.models.fields import ( 
    StringNotNullField,
    CustomDateTimeField,
    FloatNullField,
    IntegerNullField
)

from apps.workspaces.models import Workspace


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
    description = models.TextField(null=True, default='')
    tax_amount = FloatNullField(help_text='Tax amount')
    vendor_id = StringNotNullField(help_text='Vendor ID')
    code = StringNotNullField(max_length=15, help_text="unique key for each document")
    discount_amount = FloatNullField(help_text='Discount amount')
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name='Workspace Id'
    )

    class Meta:
        db_table = 'invoice'


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
    credit_card_account_id = StringNotNullField(help_text='Credit Card Account Id')
    debit_card_account_id = StringNotNullField(help_text='Debit Card Account Id')
    transaction_date = CustomDateTimeField(help_text='Transaction Date')
    description = models.TextField(null=True, default='')
    transaction_type = IntegerNullField(help_text='Transaction Type')

    class Meta:
        db_table = 'direct_cost'
