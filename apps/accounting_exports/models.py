from datetime import datetime
from typing import List
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.fields.json import KeyTextTransform
from django.db.models import Count

from fyle_accounting_mappings.models import ExpenseAttribute

from sage_desktop_api.models.fields import (
    StringNotNullField,
    StringNullField,
    CustomJsonField,
    CustomDateTimeField,
    BooleanFalseField,
    TextNotNullField,
    StringOptionsField,
    IntegerNullField
)
from apps.workspaces.models import BaseForeignWorkspaceModel, BaseModel, ExportSetting
from apps.fyle.models import Expense


ALLOWED_FIELDS = [
    'employee_email', 'report_id', 'claim_number', 'settlement_id',
    'fund_source', 'vendor', 'category', 'project', 'cost_center',
    'verified_at', 'approved_at', 'spent_at', 'expense_id', 'expense_number', 'payment_number', 'posted_at'
]

TYPE_CHOICES = (
    ('INVOICES', 'INVOICES'),
    ('DIRECT_COST', 'DIRECT_COST'),
    ('FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_REIMBURSABLE_EXPENSES'),
    ('FETCHING_CREDIT_CARD_EXPENENSES', 'FETCHING_CREDIT_CARD_EXPENENSES')
)

ERROR_TYPE_CHOICES = (('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'), ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'), ('SAGE300_ERROR', 'SAGE300_ERROR'))

EXPORT_MODE_CHOICES = (
    ('MANUAL', 'MANUAL'),
    ('AUTO', 'AUTO')
)

ALLOWED_FORM_INPUT = {
    'group_expenses_by': ['settlement_id', 'claim_number', 'report_id', 'category', 'vendor', 'expense_id', 'expense_number', 'payment_number'],
    'export_date_type': ['current_date', 'approved_at', 'spent_at', 'verified_at', 'last_spent_at', 'posted_at']
}


def _group_expenses(expenses, group_fields, workspace_id):
    """
    Group expenses based on specified fields
    """

    # Extract expense IDs from the provided expenses
    expense_ids = [expense.id for expense in expenses]

    # Retrieve expenses from the database
    expenses = Expense.objects.filter(id__in=expense_ids).all()

    # Create a dictionary to store custom fields
    custom_fields = {}

    # Iterate through group fields
    for field in group_fields:
        # Check if the field is allowed; if not, it's treated as a custom field
        if field.lower() not in ALLOWED_FIELDS:
            group_fields.pop(group_fields.index(field))

            # Retrieve the custom field information from ExpenseAttribute
            field_info = ExpenseAttribute.objects.filter(
                workspace_id=workspace_id,
                attribute_type=field.upper()
            ).first()

            if field_info:
                # Add the custom field to the dictionary with the key as its display name
                custom_fields[field_info.attribute_type.lower()] = KeyTextTransform(
                    field_info.display_name, 'custom_properties')

    # Create expense groups by grouping expenses based on specified fields and custom fields
    expense_groups = list(expenses.values(*group_fields, **custom_fields).annotate(
        total=Count('*'), expense_ids=ArrayAgg('id')))

    return expense_groups


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

    @staticmethod
    def create_expense_groups_by_report_id_fund_source(expense_objects: List[Expense], workspace_id):
        """
        Group expenses by report_id and fund_source
        """

        # Retrieve the ExportSetting for the workspace
        export_setting = ExportSetting.objects.get(workspace_id=workspace_id)

        # Initialize lists and fields for reimbursable and corporate credit card expenses
        reimbursable_expense_group_fields = export_setting.reimbursable_expense_grouped_by
        reimbursable_expenses = list(filter(lambda expense: expense.fund_source == 'PERSONAL', expense_objects))

        # Group reimbursable expenses
        expense_groups = _group_expenses(reimbursable_expenses, reimbursable_expense_group_fields, workspace_id)

        corporate_credit_card_expense_group_field = export_setting.credit_card_expense_grouped_by
        corporate_credit_card_expenses = list(filter(lambda expense: expense.fund_source == 'CCC', expense_objects))
        corporate_credit_card_expense_groups = _group_expenses(
            corporate_credit_card_expenses, corporate_credit_card_expense_group_field, workspace_id)

        # Combine reimbursable and corporate credit card expense groups
        expense_groups.extend(corporate_credit_card_expense_groups)

        for expense_group in expense_groups:
            # Determine the date field for reimbursable expenses
            if export_setting.reimbursable_expense_date == 'last_spent_at':
                expense_group['last_spent_at'] = Expense.objects.filter(id__in=expense_group['expense_ids']).order_by('-spent_at').first().spent_at

            # Determine the date field for corporate credit card expenses
            if export_setting.credit_card_expense_date == 'last_spent_at':
                expense_group['last_spent_at'] = Expense.objects.filter(id__in=expense_group['expense_ids']).order_by('-spent_at').first().spent_at

            # Get the employee name for the expense group
            employee_name = Expense.objects.filter(id__in=expense_group['expense_ids']).first().employee_name

            # Store expense IDs and remove unnecessary keys
            expense_ids = expense_group['expense_ids']
            expense_group.pop('total')
            expense_group.pop('expense_ids')

            # Format date fields according to the specified format
            for key in expense_group:
                if key in ALLOWED_FORM_INPUT['export_date_type']:
                    if expense_group[key]:
                        expense_group[key] = expense_group[key].strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        expense_group[key] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

            # Create an AccountingExport object for the expense group
            expense_group_object = AccountingExport.objects.create(
                workspace_id=workspace_id,
                fund_source=expense_group['fund_source'],
                description=expense_group,
                employee_name=employee_name
            )

            # Add related expenses to the AccountingExport object
            expense_group_object.expenses.add(*expense_ids)


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


class AccountingExportSummary(BaseModel):
    """
    Table to store accounting export summary
    """
    id = models.AutoField(primary_key=True)
    last_exported_at = CustomDateTimeField(help_text='Last exported at datetime')
    next_export_at = CustomDateTimeField(help_text='next export datetime')
    export_mode = StringOptionsField(choices=EXPORT_MODE_CHOICES, help_text='Export mode')
    total_accounting_export_count = IntegerNullField(help_text='Total count of accounting export exported')
    successful_accounting_export_count = IntegerNullField(help_text='count of successful accounting export')
    failed_accounting_export_count = IntegerNullField(help_text='count of failed accounting export')

    class Meta:
        db_table = 'accounting_export_summary'
