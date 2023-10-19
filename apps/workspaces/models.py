from django.db import models
from django.contrib.auth import get_user_model

from apps.workspaces.helpers import StringNotNullField, StringNullField, CustomDateTimeField, StringOptionsField

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
