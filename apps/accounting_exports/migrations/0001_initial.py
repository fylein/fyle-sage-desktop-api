# Generated by Django 4.1.2 on 2023-10-27 06:29

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fyle', '0001_initial'),
        ('fyle_accounting_mappings', '0023_alter_mapping_destination'),
        ('workspaces', '0002_remove_exportsetting_auto_create_vendor_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountingExport',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', sage_desktop_api.models.fields.StringOptionsField(choices=[('INVOICES', 'INVOICES'), ('DIRECT_COST', 'DIRECT_COST'), ('FETCHING_REIMBURSABLE_EXPENSES', 'FETCHING_REIMBURSABLE_EXPENSES'), ('FETCHING_CREDIT_CARD_EXPENENSES', 'FETCHING_CREDIT_CARD_EXPENENSES')], default='', help_text='Task type', max_length=255, null=True)),
                ('fund_source', sage_desktop_api.models.fields.StringNotNullField(help_text='Expense fund source', max_length=255)),
                ('mapping_errors', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, help_text='Mapping errors', null=True, size=None)),
                ('task_id', sage_desktop_api.models.fields.StringNullField(help_text='Fyle Jobs task reference', max_length=255, null=True)),
                ('description', sage_desktop_api.models.fields.CustomJsonField(default=list, help_text='Description', null=True)),
                ('status', sage_desktop_api.models.fields.StringNotNullField(help_text='Task Status', max_length=255)),
                ('detail', sage_desktop_api.models.fields.CustomJsonField(default=list, help_text='Task Response', null=True)),
                ('sage_300_errors', sage_desktop_api.models.fields.CustomJsonField(default=list, help_text='Sage 300 Errors', null=True)),
                ('exported_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='time of export', null=True)),
                ('expenses', models.ManyToManyField(help_text='Expenses under this Expense Group', to='fyle.expense')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'accounting_exports',
            },
        ),
        migrations.CreateModel(
            name='Error',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', sage_desktop_api.models.fields.StringOptionsField(choices=[('EMPLOYEE_MAPPING', 'EMPLOYEE_MAPPING'), ('CATEGORY_MAPPING', 'CATEGORY_MAPPING'), ('SAGE300_ERROR', 'SAGE300_ERROR')], default='', help_text='Error type', max_length=50, null=True)),
                ('is_resolved', sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Is resolved')),
                ('error_title', sage_desktop_api.models.fields.StringNotNullField(help_text='Error title', max_length=255)),
                ('error_detail', sage_desktop_api.models.fields.TextNotNullField(help_text='Error detail')),
                ('accounting_export', models.ForeignKey(help_text='Reference to Expense group', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounting_exports.accountingexport')),
                ('expense_attribute', models.OneToOneField(help_text='Reference to Expense Attribute', null=True, on_delete=django.db.models.deletion.PROTECT, to='fyle_accounting_mappings.expenseattribute')),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'errors',
            },
        ),
    ]
