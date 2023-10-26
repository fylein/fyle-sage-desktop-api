from django.db import models
from django.contrib.postgres.fields import ArrayField

from fyle_accounting_mappings.models import ExpenseAttribute

from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringNullField,
    CustomJsonField,
    CustomDateTimeField,
    BooleanFalseField,
    TextNotNullField,
    StringOptionsField
)
from apps.workspaces.models import BaseForeignWorkspaceModel
from apps.fyle.models import Expense


ERROR_TYPE_CHOICES = (('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'), ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'), ('SAGE_ERROR', 'SAGE_ERROR'))


class AccountingExport(BaseForeignWorkspaceModel):
    """
    Table to store accounting exports
    """
    id = models.AutoField(primary_key=True)
    type = StringNotNullField(max_length=50, help_text='Task type (FETCH_EXPENSES / INVOICES / DIRECT_COST)')
    fund_source = StringNotNullField(help_text='Expense fund source')
    mapping_errors = ArrayField(help_text='Mapping errors', base_field=models.CharField(max_length=255), blank=True, null=True)
    expenses = models.ManyToManyField(Expense, help_text="Expenses under this Expense Group")
    task_id = StringNullField(help_text='Fyle Jobs task reference')
    description = CustomJsonField(help_text='Description')
    status = StringNotNullField(help_text='Task Status')
    detail = CustomJsonField(help_text='Task Response')
    sage_intacct_errors = CustomJsonField(help_text='Sage Intacct Errors')
    exported_at = CustomDateTimeField(help_text='time of export')

    class Meta:
        db_table = 'accounting_exports'


class Error(BaseForeignWorkspaceModel):
    """
    Table to store errors
    """
    id = models.AutoField(primary_key=True)
    type = StringOptionsField(max_length=50, choices=ERROR_TYPE_CHOICES, help_text='Error type')
    accounting_export = models.ForeignKey(
        AccountingExport, on_delete=models.PROTECT,
        null=True, help_text='Reference to Expense group'
    )
    expense_attribute = models.OneToOneField(
        ExpenseAttribute, on_delete=models.PROTECT,
        null=True, help_text='Reference to Expense Attribute'
    )
    is_resolved = BooleanFalseField(help_text='Is resolved')
    error_title = StringNotNullField(help_text='Error title')
    error_detail = TextNotNullField(help_text='Error detail')

    class Meta:
        db_table = 'errors'
