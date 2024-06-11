from typing import List
from django.db import models
from datetime import datetime
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.aggregates import ArrayAgg
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


def _group_expenses(expenses: List[Expense], export_setting: ExportSetting, fund_source: str):
    """
    Group expenses based on specified fields
    """

    credit_card_expense_grouped_by = export_setting.credit_card_expense_grouped_by
    credit_card_expense_date = export_setting.credit_card_expense_date
    reimbursable_expense_grouped_by = export_setting.reimbursable_expense_grouped_by
    reimbursable_expense_date = export_setting.reimbursable_expense_date

    default_fields = ['employee_email', 'fund_source']
    report_grouping_fields = ['report_id', 'claim_number', 'corporate_card_id']
    expense_grouping_fields = ['expense_id', 'expense_number']

    # Define a mapping for fund sources and their associated group fields
    fund_source_mapping = {
        'CCC': {
            'group_by': report_grouping_fields if (export_setting.credit_card_expense_grouped_by and credit_card_expense_grouped_by == 'REPORT') else expense_grouping_fields,
            'date_field': credit_card_expense_date.lower() if (export_setting.credit_card_expense_date and credit_card_expense_date != 'LAST_SPENT_AT') else None
        },
        'PERSONAL': {
            'group_by': report_grouping_fields if (export_setting.reimbursable_expense_grouped_by and reimbursable_expense_grouped_by == 'REPORT') else expense_grouping_fields,
            'date_field': reimbursable_expense_date.lower() if (export_setting.reimbursable_expense_grouped_by and reimbursable_expense_date != 'LAST_SPENT_AT') else None
        }
    }

    # Update expense_group_fields based on the fund_source
    fund_source_data = fund_source_mapping.get(fund_source)
    group_by_field = fund_source_data.get('group_by')
    date_field = fund_source_data.get('date_field')

    default_fields.extend(group_by_field)

    if date_field and date_field != 'current_date':
        default_fields.append(date_field)

    # Extract expense IDs from the provided expenses
    expense_ids = [expense.id for expense in expenses]
    # Retrieve expenses from the database
    expenses = Expense.objects.filter(id__in=expense_ids).all()

    # Create expense groups by grouping expenses based on specified fields
    expense_groups = list(expenses.values(*default_fields).annotate(
        total=Count('*'), expense_ids=ArrayAgg('id'))
    )

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
    sage300_errors = CustomJsonField(help_text='Sage 300 Errors')
    export_id = StringNullField(help_text='id of the exported expense')
    exported_at = CustomDateTimeField(help_text='time of export')

    class Meta:
        db_table = 'accounting_exports'

    @staticmethod
    def create_accounting_export(expense_objects: List[Expense], fund_source: str, workspace_id):
        """
        Group expenses by report_id and fund_source, format date fields, and create AccountingExport objects.
        """
        # Retrieve the ExportSetting for the workspace
        export_setting = ExportSetting.objects.get(workspace_id=workspace_id)

        # Group expenses based on specified fields and fund_source
        accounting_exports = _group_expenses(expense_objects, export_setting, fund_source)

        fund_source_map = {
            'PERSONAL': 'reimbursable',
            'CCC': 'credit_card'
        }

        for accounting_export in accounting_exports:
            # Determine the date field based on fund_source
            date_field = getattr(export_setting, f"{fund_source_map.get(fund_source)}_expense_date", None).lower()
            if date_field and date_field not in ['current_date', 'last_spent_at']:
                if accounting_export[date_field]:
                    accounting_export[date_field] = accounting_export[date_field].strftime('%Y-%m-%d')
                else:
                    accounting_export[date_field] = datetime.now().strftime('%Y-%m-%d')

            # Calculate and assign 'last_spent_at' based on the chosen date field
            if date_field == 'last_spent_at':
                latest_expense = Expense.objects.filter(id__in=accounting_export['expense_ids']).order_by('-spent_at').first()
                accounting_export['last_spent_at'] = latest_expense.spent_at.strftime('%Y-%m-%d') if latest_expense else None

            # Store expense IDs and remove unnecessary keys
            expense_ids = accounting_export['expense_ids']
            accounting_export.pop('total')
            accounting_export.pop('expense_ids')

            # Create an AccountingExport object for the expense group
            accounting_export_instance = AccountingExport.objects.create(
                workspace_id=workspace_id,
                fund_source=accounting_export['fund_source'],
                description=accounting_export,
                status='EXPORT_READY'
            )

            # Add related expenses to the AccountingExport object
            accounting_export_instance.expenses.add(*expense_ids)


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
