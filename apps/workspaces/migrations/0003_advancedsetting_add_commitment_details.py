# Generated by Django 4.1.2 on 2024-02-01 20:19

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0002_sage300credential_lastexportdetail_importsetting_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='advancedsetting',
            name='add_commitment_details',
            field=sage_desktop_api.models.fields.BooleanFalseField(default=False, help_text='Add commitment details'),
        ),
    ]
