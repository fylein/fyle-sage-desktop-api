from django.db import models


class BaseExportModel(models.Model):

    """
    Base Model for Sage300 Export
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        abstract = True
