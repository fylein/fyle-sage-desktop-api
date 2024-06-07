from django.db import models

from apps.workspaces.models import BaseForeignWorkspaceModel, BaseModel
from sage_desktop_api.models.fields import (
    CustomJsonField,
    StringNotNullField,
    StringOptionsField,
    IntegerNotNullField,
    CustomDateTimeField,
    IntegerNullField
)

IMPORT_STATUS_CHOICES = (
    ('FATAL', 'FATAL'),
    ('COMPLETE', 'COMPLETE'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED')
)


class ImportLog(BaseForeignWorkspaceModel):
    """
    Table to store import logs
    """

    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    attribute_type = StringNotNullField(max_length=150, help_text='Attribute type')
    status = StringOptionsField(help_text='Status', choices=IMPORT_STATUS_CHOICES)
    error_log = CustomJsonField(help_text='Emails Selected For Email Notification')
    total_batches_count = IntegerNotNullField(help_text='Queued batches', default=0)
    processed_batches_count = IntegerNotNullField(help_text='Processed batches', default=0)
    last_successful_run_at = CustomDateTimeField(help_text='Last successful run')

    class Meta:
        db_table = 'import_logs'
        unique_together = ('workspace', 'attribute_type')

    @classmethod
    def create_import_log(self, attribute_type, workspace_id):
        """
        Create import logs set to IN_PROGRESS
        """
        import_log, _ = self.objects.update_or_create(
            workspace_id=workspace_id,
            attribute_type=attribute_type,
            defaults={
                'status': 'IN_PROGRESS'
            }
        )
        return import_log


class Version(BaseModel):
    """
    Table to store versions
    """

    id = models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)
    account = IntegerNullField(help_text='version for account')
    job = IntegerNullField(help_text='version for job')
    standard_category = IntegerNullField(help_text='version for standard category')
    standard_cost_code = IntegerNullField(help_text='version for standard costcode')
    cost_category = IntegerNullField(help_text='version for job category')
    cost_code = IntegerNullField(help_text='version for costcode')
    vendor = IntegerNullField(help_text='version for vendor')
    commitment = IntegerNullField(help_text='version for commitment')
    commitment_item = IntegerNullField(help_text='version for commitment item')

    class Meta:
        db_table = 'versions'
