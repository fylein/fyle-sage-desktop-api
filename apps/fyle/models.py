from django.db import models
from django.contrib.postgres.fields import ArrayField
from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringOptionsField,
    BooleanFalseField,
    IntegerOptionsField
)
from apps.workspaces.models import BaseForeignWorkspaceModel


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


class Reimbursement:
    """
    Creating a dummy class to be able to user
    fyle_integrations_platform_connector correctly
    """
    pass
