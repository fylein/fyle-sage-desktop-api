from django.db import models
from django.contrib.postgres.fields import ArrayField
from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringNullField,
    StringOptionsField,
    BooleanFalseField,
    IntegerOptionsField,
    CustomJsonField,
    CustomDateTimeField,
    CustomEmailField,
    FloatNullField
)
from apps.workspaces.models import BaseModel, BaseForeignWorkspaceModel


EXPENSE_FILTER_RANK = (
    (1, 1),
    (2, 2)
)

EXPENSE_FILTER_JOIN_BY = (
    ('AND', 'AND'),
    ('OR', 'OR')
)

EXPENSE_FILTER_CUSTOM_FIELD_TYPE = (
    ('SELECT', 'SELECT'),
    ('NUMBER', 'NUMBER'),
    ('TEXT', 'TEXT')
)

EXPENSE_FILTER_OPERATOR = (
    ('isnull', 'isnull'),
    ('in', 'in'),
    ('iexact', 'iexact'),
    ('icontains', 'icontains'),
    ('lt', 'lt'),
    ('lte', 'lte'),
    ('not_in', 'not_in')
)


class ExpenseFilter(BaseForeignWorkspaceModel):
    """
    Reimbursements
    """
    id = models.AutoField(primary_key=True)
    condition = StringNotNullField(help_text='Condition for the filter')
    operator = StringOptionsField(choices=EXPENSE_FILTER_OPERATOR, help_text='Operator for the filter')
    values = ArrayField(base_field=models.CharField(max_length=255), null=True, help_text='Values for the operator')
    rank = IntegerOptionsField(choices=EXPENSE_FILTER_RANK, help_text='Rank for the filter')
    join_by = StringOptionsField(choices=EXPENSE_FILTER_JOIN_BY, max_length=3, help_text='Used to join the filter (AND/OR)')
    is_custom = BooleanFalseField(help_text='Custom Field or not')
    custom_field_type = StringOptionsField(help_text='Custom field type', choices=EXPENSE_FILTER_CUSTOM_FIELD_TYPE)

    class Meta:
        db_table = 'expense_filters'


class Expense(BaseModel):
    """
    Expense
    """
    id = models.AutoField(primary_key=True)
    employee_email = CustomEmailField(help_text='Email id of the Fyle employee')
    employee_name = StringNullField(help_text='Name of the Fyle employee')
    category = StringNullField(help_text='Fyle Expense Category')
    sub_category = StringNullField(help_text='Fyle Expense Sub-Category')
    project = StringNullField(help_text='Project')
    expense_id = StringNotNullField(unique=True, help_text='Expense ID')
    org_id = StringNullField(help_text='Organization ID')
    expense_number = StringNotNullField(help_text='Expense Number')
    claim_number = StringNotNullField(help_text='Claim Number')
    amount = models.FloatField(help_text='Home Amount')
    currency = StringNotNullField(max_length=5, help_text='Home Currency')
    foreign_amount = models.FloatField(null=True, help_text='Foreign Amount')
    foreign_currency = StringNotNullField(max_length=5, help_text='Foreign Currency')
    settlement_id = StringNullField(help_text='Settlement ID')
    reimbursable = BooleanFalseField(help_text='Expense reimbursable or not')
    state = StringNotNullField(help_text='Expense state')
    vendor = StringNotNullField(help_text='Vendor')
    cost_center = StringNullField(help_text='Fyle Expense Cost Center')
    corporate_card_id = StringNullField(help_text='Corporate Card ID')
    purpose = models.TextField(null=True, blank=True, help_text='Purpose')
    report_id = StringNotNullField(help_text='Report ID')
    billable = BooleanFalseField(help_text='Expense billable or not')
    file_ids = ArrayField(base_field=models.CharField(max_length=255), null=True, help_text='File IDs')
    spent_at = CustomDateTimeField(help_text='Expense spent at')
    approved_at = CustomDateTimeField(help_text='Expense approved at')
    posted_at = CustomDateTimeField(help_text='Date when the money is taken from the bank')
    expense_created_at = CustomDateTimeField(help_text='Expense created at')
    expense_updated_at = CustomDateTimeField(help_text='Expense created at')
    fund_source = StringNotNullField(help_text='Expense fund source')
    verified_at = CustomDateTimeField(help_text='Report verified at')
    custom_properties = CustomJsonField(help_text="Custom Properties")
    tax_amount = FloatNullField(help_text='Tax Amount')
    tax_group_id = StringNullField(help_text='Tax Group ID')
    exported = BooleanFalseField(help_text='Expense reimbursable or not')
    previous_export_state = StringNullField(max_length=255, help_text='Previous export state')
    accounting_export_summary = CustomJsonField(default=dict, help_text='Accounting Export Summary')


class Reimbursement:
    """
    Creating a dummy class to be able to use
    fyle_integrations_platform_connector correctly
    """
    pass
