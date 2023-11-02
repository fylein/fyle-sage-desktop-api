from typing import Dict, List
from django.db import models

from fyle_accounting_mappings.models import (
    DestinationAttribute
)

from apps.workspaces.models import BaseModel, BaseForeignWorkspaceModel
from sage_desktop_api.models.fields import (
    StringNotNullField,
    CustomDateTimeField,
    FloatNullField,
    IntegerNullField,
    TextNotNullField,
    BooleanFalseField
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


class Sage300Categories(BaseForeignWorkspaceModel):
    """
    Categories Table Model Class
    """

    id = models.AutoField(primary_key=True)
    job_id = StringNotNullField(help_text='Sage300 Job Id')
    job_name = StringNotNullField(help_text='Sage300 Job Name')
    cost_code_id = StringNotNullField(help_text='Sage300 Cost Code Id')
    cost_code_name = StringNotNullField(help_text='Sage300 Cost Code Name')
    name = StringNotNullField(help_text='Sage300 Cost Type Name')
    category_id = StringNotNullField(help_text='Sage300 Category Id')
    status = BooleanFalseField(help_text='Sage300 Cost Type Status')

    class Meta:
        db_table = 'sage300_categories'

    @staticmethod
    def bulk_create_or_update(categories_generator: List[Dict], workspace_id: int):
        """
        Bulk create or update cost types
        """

        list_of_categories = []
        for categories in categories_generator:
            list_of_categories.append(categories)

        record_number_list = [category.id for category in list_of_categories]

        filters = {
            'category_id__in': record_number_list,
            'workspace_id': workspace_id
        }

        existing_categories = Sage300Categories.objects.filter(**filters).values(
            'id',
            'category_id',
            'name',
            'status'
        )

        existing_cost_type_record_numbers = []
        primary_key_map = {}

        for existing_category in existing_categories:
            existing_cost_type_record_numbers.append(existing_category['category_id'])
            primary_key_map[existing_category['category_id']] = {
                'id': existing_category['id'],
                'name': existing_category['name'],
                'status': existing_category['status'],
            }

        category_to_be_created = []
        category_to_be_updated = []

        # Retrieve job names and cost code names in a single query
        cost_code_ids = [category.cost_code_id for category in list_of_categories]
        job_ids = [category.job_id for category in list_of_categories]

        job_name_mapping = {attr.destination_id: attr.value for attr in DestinationAttribute.objects.filter(destination_id__in=job_ids, workspace_id=workspace_id)}
        cost_code_name_mapping = {attr.destination_id: attr.value for attr in DestinationAttribute.objects.filter(destination_id__in=cost_code_ids, workspace_id=workspace_id)}

        for category in list_of_categories:
            job_name = job_name_mapping.get(category.job_id)
            cost_code_name = cost_code_name_mapping.get(category.cost_code_id)
            category_object = Sage300Categories(
                job_id=category.job_id,
                job_name=job_name,
                cost_code_id=category.cost_code_id,
                cost_code_name=cost_code_name,
                name=category.name,
                status=category.is_active,
                category_id=category.id,
                workspace_id=workspace_id
            )

            if category.id not in existing_cost_type_record_numbers:
                category_to_be_created.append(category_object)

            elif category.id in primary_key_map.keys() and (
                category.name != primary_key_map[category.id]['name'] or category.is_active != primary_key_map[category.id]['status']
            ):
                category_object.id = primary_key_map[category.id]['category_id']
                category_to_be_updated.append(category_object)

        if category_to_be_created:
            Sage300Categories.objects.bulk_create(category_to_be_created, batch_size=2000)

        if category_to_be_updated:
            Sage300Categories.objects.bulk_update(
                category_to_be_updated, fields=[
                    'job_id', 'job_name', 'cost_code_id', 'cost_code_name',
                    'name', 'status', 'category_id'
                ],
                batch_size=2000
            )
