from django.db import models

from apps.workspaces.models import BaseModel
from sage_desktop_api.models.fields import (
    CustomJsonField,
    StringNotNullField,
    StringOptionsField,
    IntegerNotNullField,
    StringNullField,
    CustomDateTimeField
)

IMPORT_STATUS_CHOICES = (
    ('FATAL', 'FATAL'),
    ('COMPLETE', 'COMPLETE'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED')
)


class ImportLog(BaseModel):
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
    accounts_version = StringNullField(help_text='latest sync version of accounts')
    job_version = StringNullField(help_text='latest sync version of job')
    categories_version = StringNullField(help_text='latest sync version of categories')
    cost_code_version = StringNullField(help_text='latest sync version of cost code')
    vendor_version = StringNullField(help_text='latest sync version of vendor')

    class Meta:
        db_table = 'import_logs'
        unique_together = ('workspace', 'attribute_type')
