# Generated by Django 4.1.2 on 2024-07-15 12:29

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sage300', '0005_purchaseinvoicelineitems_accounts_payable_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseinvoicelineitems',
            name='expense_account_id',
            field=sage_desktop_api.models.fields.StringNullField(help_text='destination id of accounts expense account', max_length=255, null=True),
        ),
    ]
