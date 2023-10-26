# Generated by Django 3.1.14 on 2023-10-26 10:54

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exportsetting',
            name='auto_create_vendor',
        ),
        migrations.RemoveField(
            model_name='exportsetting',
            name='default_credit_card_account_id',
        ),
        migrations.RemoveField(
            model_name='exportsetting',
            name='default_credit_card_account_name',
        ),
        migrations.AddField(
            model_name='advancedsetting',
            name='auto_create_vendor',
            field=sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Auto create vendor'),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='auto_map_employees',
            field=sage_desktop_api.models.fields.BooleanTrueField(default=True, help_text='Auto map employees'),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='default_ccc_credit_card_account_id',
            field=sage_desktop_api.models.fields.StringNullField(help_text='CCC Credit Card Account ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='default_ccc_credit_card_account_name',
            field=sage_desktop_api.models.fields.StringNullField(help_text='CCC Credit card account name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='default_reimbursable_credit_card_account_id',
            field=sage_desktop_api.models.fields.StringNullField(help_text='Reimbursable Credit card account name', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='exportsetting',
            name='default_reimbursable_credit_card_account_name',
            field=sage_desktop_api.models.fields.StringNullField(help_text='Reimbursable Credit card account name', max_length=255, null=True),
        ),
    ]
