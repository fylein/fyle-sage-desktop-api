# Generated by Django 3.1.14 on 2023-10-26 10:54

import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0002_auto_20231026_1054'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseFilter',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('condition', sage_desktop_api.models.fields.StringNotNullField(help_text='Condition for the filter', max_length=255)),
                ('operator', sage_desktop_api.models.fields.StringOptionsField(choices=[('isnull', 'isnull'), ('in', 'in'), ('iexact', 'iexact'), ('icontains', 'icontains'), ('lt', 'lt'), ('lte', 'lte'), ('not_in', 'not_in')], default='', help_text='Operator for the filter', max_length=255, null=True)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), help_text='Values for the operator', null=True, size=None)),
                ('rank', sage_desktop_api.models.fields.IntegerOptionsField(choices=[(1, 1), (2, 2)], default='', help_text='Rank for the filter', null=True)),
                ('join_by', sage_desktop_api.models.fields.StringOptionsField(choices=[('AND', 'AND'), ('OR', 'OR')], default='', help_text='Used to join the filter (AND/OR)', max_length=3, null=True)),
                ('is_custom', sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Custom Field or not')),
                ('custom_field_type', sage_desktop_api.models.fields.StringOptionsField(choices=[('SELECT', 'SELECT'), ('NUMBER', 'NUMBER'), ('TEXT', 'TEXT')], default='', help_text='Custom field type', max_length=255, null=True)),
                ('workspace', models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'expense_filters',
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Created at datetime')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Updated at datetime')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('employee_email', sage_desktop_api.models.fields.CustomEmailField(help_text='Email id of the Fyle employee', max_length=254, validators=[django.core.validators.EmailValidator()])),
                ('employee_name', sage_desktop_api.models.fields.StringNullField(help_text='Name of the Fyle employee', max_length=255, null=True)),
                ('category', sage_desktop_api.models.fields.StringNullField(help_text='Fyle Expense Category', max_length=255, null=True)),
                ('sub_category', sage_desktop_api.models.fields.StringNullField(help_text='Fyle Expense Sub-Category', max_length=255, null=True)),
                ('project', sage_desktop_api.models.fields.StringNullField(help_text='Project', max_length=255, null=True)),
                ('expense_id', sage_desktop_api.models.fields.StringNotNullField(help_text='Expense ID', max_length=255, unique=True)),
                ('org_id', sage_desktop_api.models.fields.StringNullField(help_text='Organization ID', max_length=255, null=True)),
                ('expense_number', sage_desktop_api.models.fields.StringNotNullField(help_text='Expense Number', max_length=255)),
                ('claim_number', sage_desktop_api.models.fields.StringNotNullField(help_text='Claim Number', max_length=255)),
                ('amount', models.FloatField(help_text='Home Amount')),
                ('currency', sage_desktop_api.models.fields.StringNotNullField(help_text='Home Currency', max_length=5)),
                ('foreign_amount', models.FloatField(help_text='Foreign Amount', null=True)),
                ('foreign_currency', sage_desktop_api.models.fields.StringNotNullField(help_text='Foreign Currency', max_length=5)),
                ('settlement_id', sage_desktop_api.models.fields.StringNullField(help_text='Settlement ID', max_length=255, null=True)),
                ('reimbursable', sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Expense reimbursable or not')),
                ('state', sage_desktop_api.models.fields.StringNotNullField(help_text='Expense state', max_length=255)),
                ('vendor', sage_desktop_api.models.fields.StringNotNullField(help_text='Vendor', max_length=255)),
                ('cost_center', sage_desktop_api.models.fields.StringNullField(help_text='Fyle Expense Cost Center', max_length=255, null=True)),
                ('corporate_card_id', sage_desktop_api.models.fields.StringNullField(help_text='Corporate Card ID', max_length=255, null=True)),
                ('purpose', models.TextField(blank=True, help_text='Purpose', null=True)),
                ('report_id', sage_desktop_api.models.fields.StringNotNullField(help_text='Report ID', max_length=255)),
                ('billable', sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Expense billable or not')),
                ('file_ids', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), help_text='File IDs', null=True, size=None)),
                ('spent_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Expense spent at', null=True)),
                ('approved_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Expense approved at', null=True)),
                ('posted_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Date when the money is taken from the bank', null=True)),
                ('expense_created_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Expense created at', null=True)),
                ('expense_updated_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Expense created at', null=True)),
                ('fund_source', sage_desktop_api.models.fields.StringNotNullField(help_text='Expense fund source', max_length=255)),
                ('verified_at', sage_desktop_api.models.fields.CustomDateTimeField(help_text='Report verified at', null=True)),
                ('custom_properties', sage_desktop_api.models.fields.CustomJsonField(default=list, help_text='Custom Properties', null=True)),
                ('tax_amount', sage_desktop_api.models.fields.FloatNullField(help_text='Tax Amount', null=True)),
                ('tax_group_id', sage_desktop_api.models.fields.StringNullField(help_text='Tax Group ID', max_length=255, null=True)),
                ('exported', sage_desktop_api.models.fields.BooleanFalseField(default=True, help_text='Expense reimbursable or not')),
                ('previous_export_state', sage_desktop_api.models.fields.StringNullField(help_text='Previous export state', max_length=255, null=True)),
                ('accounting_export_summary', sage_desktop_api.models.fields.CustomJsonField(default=list, help_text='Accounting Export Summary', null=True)),
                ('workspace', models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace')),
            ],
            options={
                'db_table': 'expenses',
            },
        ),
    ]
