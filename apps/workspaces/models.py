from django.db import models
from django.contrib.auth import get_user_model

from sage_desktop_api.helpers import (
    StringNotNullField, 
    StringNullField, 
    CustomDateTimeField, 
    StringOptionsField, 
    TextNotNullField, 
    BooleanFalseField
)

User = get_user_model()

ONBOARDING_STATE_CHOICES = (
    ('CONNECTION', 'CONNECTION'),
    ('EXPORT_SETTINGS', 'EXPORT_SETTINGS'),
    ('IMPORT_SETTINGS', 'IMPORT_SETTINGS'),
    ('ADVANCED_CONFIGURATION', 'ADVANCED_CONFIGURATION'),
    ('COMPLETE', 'COMPLETE')
)


def get_default_onboarding_state():
    return 'EXPORT_SETTINGS'


class Workspace(models.Model):
    """
    Workspace model
    """
    id = models.AutoField(primary_key=True)
    name = StringNotNullField(help_text='Name of the workspace')
    user = models.ManyToManyField(User, help_text='Reference to users table')
    org_id = models.CharField(max_length=255, help_text='org id', unique=True)
    last_synced_at = CustomDateTimeField(help_text='Datetime when expenses were pulled last')
    ccc_last_synced_at = CustomDateTimeField(help_text='Datetime when ccc expenses were pulled last')
    source_synced_at = CustomDateTimeField(help_text='Datetime when source dimensions were pulled')
    destination_synced_at = CustomDateTimeField(help_text='Datetime when destination dimensions were pulled')
    onboarding_state = StringOptionsField(
        max_length=50, choices=ONBOARDING_STATE_CHOICES, default=get_default_onboarding_state,
        help_text='Onboarding status of the workspace'
    )
    sage300_accounts_last_synced_at = CustomDateTimeField(help_text='sage accounts last synced at time')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspaces'


class BaseModel(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        abstract = True


class FyleCredential(BaseModel):
    """
    Table to store Fyle credentials
    """
    refresh_token = TextNotNullField(help_text='Fyle refresh token')
    cluster_domain = StringNullField(help_text='Fyle cluster domain')

    class Meta:
        db_table = 'fyle_credentials'


class Sage300Credentials(BaseModel):
    """
    Table to store Business Central credentials
    """
    identifier = StringNotNullField(help_text='sage300 identifier')
    username = StringNotNullField(help_text='sage300 username')
    password = StringNotNullField(help_text='sage300 password')
    api_key = StringNotNullField(help_text='sage300 api key')
    api_secret = StringNotNullField(help_text='sage300 api secret')

    class Meta:
        db_table = 'sage300_credentials'


# Reimbursable Expense Choices
REIMBURSABLE_EXPENSE_EXPORT_TYPE_CHOICES = (
    ('PURCHASE_INVOICE', 'PURCHASE_INVOICE'),
    ('DIRECT_COST', 'DIRECT_COST')
)

REIMBURSABLE_EXPENSE_STATE_CHOICES = (
    ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING'),
    ('CLOSED', 'CLOSED')
)

REIMBURSABLE_EXPENSES_GROUPED_BY_CHOICES = (
    ('REPORT', 'report_id'),
    ('EXPENSE', 'expense_id')
)

REIMBURSABLE_EXPENSES_DATE_TYPE_CHOICES = (
    ('LAST_SPENT_AT', 'last_spent_at'),
    ('CREATED_AT', 'created_at'),
    ('SPENT_AT', 'spent_at')
)

# Credit Card Expense Choices
CREDIT_CARD_EXPENSE_EXPORT_TYPE_CHOICES = (
    ('JOURNAL_ENTRY', 'JOURNAL_ENTRY'),
)

CREDIT_CARD_EXPENSE_STATE_CHOICES = (
    ('APPROVED', 'APPROVED'),
    ('PAYMENT_PROCESSING', 'PAYMENT_PROCESSING'),
    ('PAID', 'PAID')
)

CREDIT_CARD_EXPENSES_GROUPED_BY_CHOICES = (
    ('REPORT', 'report_id'),
    ('EXPENSE', 'expense_id')
)

CREDIT_CARD_EXPENSES_DATE_TYPE_CHOICES = (
    ('LAST_SPENT_AT', 'last_spent_at'),
    ('POSTED_AT', 'posted_at'),
    ('CREATED_AT', 'created_at')
)


class ExportSettings(BaseModel):
    """
    Table to store export settings
    """
    # Reimbursable Expenses Export Settings
    reimbursable_expenses_export_type = StringOptionsField(
        choices=REIMBURSABLE_EXPENSE_EXPORT_TYPE_CHOICES,
    )
    default_bank_account_name = StringNullField(help_text='Bank account name')
    default_back_account_id = StringNullField(help_text='Bank Account ID')
    reimbursable_expense_state = StringOptionsField(
        choices=REIMBURSABLE_EXPENSE_STATE_CHOICES
    )
    reimbursable_expense_date = StringOptionsField(
        choices=REIMBURSABLE_EXPENSES_DATE_TYPE_CHOICES
    )
    reimbursable_expense_grouped_by = StringOptionsField(
        choices=REIMBURSABLE_EXPENSES_GROUPED_BY_CHOICES
    )
    # Credit Card Expenses Export Settings
    credit_card_expense_export_type = StringOptionsField(
        choices=CREDIT_CARD_EXPENSE_EXPORT_TYPE_CHOICES
    )
    credit_card_expense_state = StringOptionsField(
        choices=CREDIT_CARD_EXPENSE_STATE_CHOICES
    )
    default_credit_card_account_name = StringNullField(help_text='Credit card account name')
    default_credit_card_account_id = StringNullField(help_text='Credit Card Account ID')
    credit_card_expense_grouped_by = StringOptionsField(
        choices=CREDIT_CARD_EXPENSES_GROUPED_BY_CHOICES
    )
    credit_card_expense_date = StringOptionsField(
        choices=CREDIT_CARD_EXPENSES_DATE_TYPE_CHOICES
    )
    default_vendor_name = StringNullField(help_text='default Vendor Name')
    default_vendor_id = StringNullField(help_text='default Vendor Id')
    auto_create_vendor = BooleanFalseField(help_text='Auto create vendor')

    class Meta:
        db_table = 'export_settings'
