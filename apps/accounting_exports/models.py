from django.db import models
from django.contrib.postgres.fields import ArrayField
from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringNullField,
    CustomJsonField,
    CustomDateTimeField
)
from apps.workspaces.models import BaseModel
from apps.fyle.models import Expense
from apps.sage300.models import Invoice, DirectCost



class AccountingExport(BaseModel):
    """
    Table to store accounting exports
    """
    id = models.AutoField(primary_key=True)
    type = StringNotNullField(max_length=50, help_text='Task type (FETCH_EXPENSES / INVOICES / DIRECT_COST)')
    fund_source = StringNotNullField(help_text='Expense fund source')
    mapping_errors = ArrayField()
    expenses = models.ManyToManyField(Expense, help_text="Expenses under this Expense Group")
    task_id = StringNullField(help_text='Fyle Jobs task reference')
    description = CustomJsonField(help_text='Description')
    status = StringNotNullField(help_text='Task Status')
    detail = CustomJsonField(help_text='Task Response')
    sage_intacct_errors = CustomJsonField(help_text='Sage Intacct Errors')
    exported_at = CustomDateTimeField(help_text='time of export')

    class Meta:
        db_table = 'accounting_exports'