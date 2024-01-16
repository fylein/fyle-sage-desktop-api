from datetime import datetime
from typing import Optional

from django.db import models
from django.db.models import Sum
from fyle_accounting_mappings.models import ExpenseAttribute, Mapping, MappingSetting, EmployeeMapping, DestinationAttribute

from apps.accounting_exports.models import AccountingExport
from apps.fyle.models import DependentFieldSetting, Expense
from apps.sage300.exports.helpers import get_filtered_mapping
from apps.workspaces.models import AdvancedSetting, FyleCredential, Workspace, ExportSetting


class BaseExportModel(models.Model):
    """
    Base Model for Sage300 Export
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')

    class Meta:
        abstract = True

    def get_expense_purpose(workspace_id, lineitem: Expense, category: str, advance_setting: AdvancedSetting) -> str:
        workspace = Workspace.objects.get(id=workspace_id)
        org_id = workspace.org_id

        fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
        cluster_domain = fyle_credentials.cluster_domain
        workspace.cluster_domain = cluster_domain
        workspace.save()

        expense_link = '{0}/app/admin/#/enterprise/view_expense/{1}?org_id={2}'.format(
            cluster_domain, lineitem.expense_id, org_id
        )

        memo_structure = advance_setting.expense_memo_structure

        details = {
            'employee_email': lineitem.employee_email,
            'merchant': '{0}'.format(lineitem.vendor) if lineitem.vendor else '',
            'category': '{0}'.format(category) if lineitem.category else '',
            'purpose': '{0}'.format(lineitem.purpose) if lineitem.purpose else '',
            'report_number': '{0}'.format(lineitem.claim_number),
            'spent_on': '{0}'.format(lineitem.spent_at.date()) if lineitem.spent_at else '',
            'expense_link': expense_link
        }

        purpose = ''

        for id, field in enumerate(memo_structure):
            if field in details:
                purpose += details[field]
                if id + 1 != len(memo_structure):
                    purpose = '{0} - '.format(purpose)

        return purpose

    def get_vendor_id(accounting_export: AccountingExport):
        # Retrieve export settings for the given workspace
        export_settings = ExportSetting.objects.get(workspace_id=accounting_export.workspace_id)

        # Extract the description from the accounting export
        description = accounting_export.description

        # Initialize vendor_id to None
        vendor_id = None

        # Check if the fund source is 'PERSONAL'
        if accounting_export.fund_source == 'PERSONAL':
            # Retrieve the vendor using EmployeeMapping
            vendor = EmployeeMapping.objects.filter(
                source_employee__value=description.get('employee_email'),
                workspace_id=accounting_export.workspace_id
            ).values_list('destination_vendor__destination_id', flat=True).first()

            # Update vendor_id with the retrieved vendor
            vendor_id = vendor

        # Check if the fund source is 'CCC'
        elif accounting_export.fund_source == 'CCC':
            # Retrieve the vendor from the first expense
            expense_vendor = accounting_export.expenses.first().vendor

            # Query DestinationAttribute for the vendor with case-insensitive search
            if expense_vendor:
                vendor = DestinationAttribute.objects.filter(
                    workspace_id=accounting_export.workspace_id,
                    value__icontains=expense_vendor,
                    attribute_type='VENDOR'
                ).values_list('destination_id', flat=True).first()
            else:
                vendor = export_settings.default_vendor_id

            # Update vendor_id with the retrieved vendor or default to export settings
            vendor_id = vendor

        # Return the determined vendor_id
        return vendor_id

    def get_total_amount(accounting_export: AccountingExport):
        """
         Calculate the total amount of expenses associated with a given AccountingExport

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance for which to calculate the total amount.

        Returns:
        - float: The total amount of expenses associated with the provided AccountingExport.
        """

        # Using the related name 'expenses' to access the expenses associated with the given AccountingExport
        total_amount = accounting_export.expenses.aggregate(Sum('amount'))['amount__sum']

        # If there are no expenses for the given AccountingExport, 'total_amount' will be None
        # Handle this case by returning 0 or handling it as appropriate for your application
        return total_amount or 0.0

    def get_invoice_date(accounting_export: AccountingExport) -> str:
        """
        Get the invoice date from the provided AccountingExport.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing the description field.

        Returns:
        - str: The invoice date as a string in the format '%Y-%m-%dT%H:%M:%S'.
        """
        # Check for specific keys in the 'description' field and return the corresponding value
        if 'spent_at' in accounting_export.description and accounting_export.description['spent_at']:
            return accounting_export.description['spent_at']
        elif 'approved_at' in accounting_export.description and accounting_export.description['approved_at']:
            return accounting_export.description['approved_at']
        elif 'verified_at' in accounting_export.description and accounting_export.description['verified_at']:
            return accounting_export.description['verified_at']
        elif 'last_spent_at' in accounting_export.description and accounting_export.description['last_spent_at']:
            return accounting_export.description['last_spent_at']
        elif 'posted_at' in accounting_export.description and accounting_export.description['posted_at']:
            return accounting_export.description['posted_at']

        # If none of the expected keys are present or if the values are empty, return the current date and time
        return datetime.now().strftime("%Y-%m-%d")

    def get_job_id(accounting_export: AccountingExport, expense: Expense):
        """
        Get the job ID based on the provided AccountingExport and Expense.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing workspace information.
        - expense (Expense): The Expense instance containing information for job ID retrieval.

        Returns:
        - Optional[str]: The job ID as a string if found, otherwise None.
        """

        job_id = None

        # Retrieve mapping settings for job
        job_settings: MappingSetting = MappingSetting.objects.filter(
            workspace_id=accounting_export.workspace_id,
            destination_field='JOB'
        ).first()

        if job_settings:
            # Determine the source value based on the configured source field
            if job_settings.source_field == 'PROJECT':
                source_value = expense.project
            elif job_settings.source_field == 'COST_CENTER':
                source_value = expense.cost_center
            else:
                attribute = ExpenseAttribute.objects.filter(attribute_type=job_settings.source_field).first()
                source_value = expense.custom_properties.get(attribute.display_name, None)

            # Check for a mapping based on the source value
            mapping: Mapping = Mapping.objects.filter(
                source_type=job_settings.source_field,
                destination_type='JOB',
                source__value=source_value,
                workspace_id=accounting_export.workspace_id
            ).first()

            # If a mapping is found, retrieve the destination job ID
            if mapping:
                job_id = mapping.destination.destination_id

        return job_id

    def get_commitment_id(accounting_export: AccountingExport, expense: Expense):
        """
        Get the commitment ID based on the provided AccountingExport and Expense.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing workspace information.
        - expense (Expense): The Expense instance containing information for job ID retrieval.

        Returns:
        - Optional[str]: The commitment ID as a string if found, otherwise None.
        """

        commitment_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=accounting_export.workspace_id,
            destination_field='COMMITMENT'
        ).first()

        commitment_id = None
        source_id = None

        if accounting_export and commitment_setting:
            if expense:
                if commitment_setting.source_field == 'PROJECT':
                    source_id = expense.project_id
                    source_value = expense.project
                elif commitment_setting.source_field == 'COST_CENTER':
                    source_value = expense.cost_center
                else:
                    attribute = ExpenseAttribute.objects.filter(commitment_setting=expense.source_field).first()
                    source_value = expense.custom_properties.get(attribute.display_name, None)
            else:
                source_value = accounting_export.description[accounting_export.source_field.lower()]

            mapping: Mapping = get_filtered_mapping(
                commitment_setting.source_field, 'COMMITMENT', accounting_export.workspace_id, source_value, source_id
            )

            if mapping:
                commitment_id = mapping.destination.destination_id
        return commitment_id

    def get_cost_code_id(accounting_export: AccountingExport, lineitem: Expense, dependent_field_setting: DependentFieldSetting, job_id: str):
        from apps.sage300.models import CostCategory
        cost_code_id = None

        selected_cost_code = lineitem.custom_properties.get(dependent_field_setting.cost_code_field_name, None)
        cost_code = CostCategory.objects.filter(
            workspace_id=accounting_export.workspace_id,
            cost_code_name=selected_cost_code,
            job_id=job_id
        ).first()

        if cost_code:
            cost_code_id = cost_code.cost_code_id

        return cost_code_id

    def get_cost_category_id(accounting_export: AccountingExport, lineitem: Expense, dependent_field_setting: DependentFieldSetting, project_id: str, cost_code_id: str):
        from apps.sage300.models import CostCategory
        cost_category_id = None

        selected_cost_category = lineitem.custom_properties.get(dependent_field_setting.cost_category_field_name, None)
        cost_category = CostCategory.objects.filter(
            workspace_id=accounting_export.workspace_id,
            cost_code_id=cost_code_id,
            job_id=project_id,
            name=selected_cost_category
        ).first()

        if cost_category:
            cost_category_id = cost_category.cost_category_id

        return cost_category_id

    def get_standard_category_id(accounting_export: AccountingExport, expense: Expense) -> Optional[str]:
        """
        Get the standard category ID based on the provided AccountingExport and Expense.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing workspace information.
        - expense (Expense): The Expense instance containing information for standard category ID retrieval.

        Returns:
        - Optional[str]: The standard category ID as a string if found, otherwise None.
        """
        standard_category_id = None

        # Retrieve mapping settings for standard category
        standard_category_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=accounting_export.workspace_id,
            destination_field='STANDARD_CATEGORY'
        ).first()

        if standard_category_setting:
            # Retrieve the attribute corresponding to the source field
            attribute = ExpenseAttribute.objects.filter(attribute_type=standard_category_setting.source_field).first()

            # Determine the source value based on the configured source field
            source_value = expense.custom_properties.get(attribute.display_name, None)

            # Check for a mapping based on the source value
            mapping: Mapping = Mapping.objects.filter(
                source_type=standard_category_setting.source_field,
                destination_type='STANDARD_CATEGORY',
                source__value=source_value,
                workspace_id=accounting_export.workspace_id
            ).first()

            # If a mapping is found, retrieve the destination standard category ID
            if mapping:
                standard_category_id = mapping.destination.destination_id

        return standard_category_id

    def get_standard_cost_code_id(accounting_export: AccountingExport, expense: Expense):
        """
        Get the standard cost code ID based on the provided AccountingExport and Expense.

        Parameters:
        - accounting_export (AccountingExport): The AccountingExport instance containing workspace information.
        - expense (Expense): The Expense instance containing information for standard category ID retrieval.

        Returns:
        - Optional[str]: The standard cost code ID as a string if found, otherwise None.
        """
        standard_cost_code_id = None

        # Retrieve mapping settings for standard cost code
        standard_cost_code_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=accounting_export.workspace_id,
            destination_field='STANDARD_COST_CODE'
        ).first()

        if standard_cost_code_setting:
            # Retrieve the attribute corresponding to the source field
            attribute = ExpenseAttribute.objects.filter(attribute_type=standard_cost_code_setting.source_field).first()

            # Determine the source value based on the configured source field
            source_value = expense.custom_properties.get(attribute.display_name, None)

            # Check for a mapping based on the source value
            mapping: Mapping = Mapping.objects.filter(
                source_type=standard_cost_code_setting.source_field,
                destination_type='STANDARD_COST_CODE',
                source__value=source_value,
                workspace_id=accounting_export.workspace_id
            ).first()

            # If a mapping is found, retrieve the destination standard cost code ID
            if mapping:
                standard_cost_code_id = mapping.destination.destination_id

        return standard_cost_code_id
