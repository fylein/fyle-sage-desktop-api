# Generated by Django 4.1.2 on 2024-06-25 05:00

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounting_exports', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountingexport',
            name='type',
            field=sage_desktop_api.models.fields.StringOptionsField(choices=[('PURCHASE_INVOICE', 'PURCHASE_INVOICE'), ('DIRECT_COST', 'DIRECT_COST'), ('FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_REIMBURSABLE_EXPENSES'), ('FETCHING_CREDIT_CARD_EXPENENSES', 'FETCHING_CREDIT_CARD_EXPENENSES')], default='', help_text='Task type', max_length=255, null=True),
        ),
    ]
