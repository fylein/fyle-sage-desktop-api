from django.db import models
from django.contrib.auth import get_user_model

from sage_desktop_api.helpers import (
        StringNotNullField,
        StringNullField,
        CustomDateTimeField,
        StringOptionsField,
        BooleanFalseField,
        TextNotNullField
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
    fyle_currency = StringNullField(max_length=5, help_text='Fyle Currency')
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


class ImportSetting(BaseModel):
    """
    Table to store Import setting
    """

    import_categories = BooleanFalseField(help_text='toggle for import of chart of accounts from sage300')
    import_vendors_as_merchants = BooleanFalseField(help_text='toggle for import of vendors as merchant from sage300')
    
    class Meta:
	    db_table = 'import_settings'
