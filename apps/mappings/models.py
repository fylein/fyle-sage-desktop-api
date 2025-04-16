from django.db import models

from apps.workspaces.models import BaseModel
from sage_desktop_api.models.fields import (
    IntegerNullField
)


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
