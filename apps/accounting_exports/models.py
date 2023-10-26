from django.db import models
from django.contrib.postgres.fields import ArrayField
from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringNullField,
    CustomJsonField,
    CustomDateTimeField,
    StringOptionsField
)
from apps.workspaces.models import BaseForeignWorkspaceModel
from apps.fyle.models import Expense

TYPE_CHOICES = (
    ('INVOICES', 'INVOICES'),
    ('DIRECT_COST', 'DIRECT_COST'),
    ('FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_REIMBURSABLE_EXPENSES'),
    ('FETCHING_CREDIT_CARD_EXPENENSES', 'FETCHING_CREDIT_CARD_EXPENENSES')
)


class AccountingExport(BaseForeignWorkspaceModel):
    """
    Table to store accounting exports
    """
    id = models.AutoField(primary_key=True)
    type = StringOptionsField(choices=TYPE_CHOICES, help_text='Task type')
    fund_source = StringNotNullField(help_text='Expense fund source')
    mapping_errors = ArrayField(help_text='Mapping errors', base_field=models.CharField(max_length=255), blank=True, null=True)
    expenses = models.ManyToManyField(Expense, help_text="Expenses under this Expense Group")
    task_id = StringNullField(help_text='Fyle Jobs task reference')
    description = CustomJsonField(help_text='Description')
    status = StringNotNullField(help_text='Task Status')
    detail = CustomJsonField(help_text='Task Response')
    sage_300_errors = CustomJsonField(help_text='Sage 300 Errors')
    exported_at = CustomDateTimeField(help_text='time of export')

    class Meta:
        db_table = 'accounting_exports'
