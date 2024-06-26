# Generated by Django 4.1.2 on 2024-06-25 05:13

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sage300', '0004_rename_accounts_payable_account_id_purchaseinvoicelineitems_expense_account_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinvoicelineitems',
            name='accounts_payable_id',
            field=sage_desktop_api.models.fields.StringNullField(help_text='destination id of accounts payable account', max_length=255, null=True),
        ),
    ]
