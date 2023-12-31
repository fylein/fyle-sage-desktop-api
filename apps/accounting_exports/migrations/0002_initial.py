# Generated by Django 4.1.2 on 2023-12-11 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fyle', '0001_initial'),
        ('workspaces', '0001_initial'),
        ('accounting_exports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountingexport',
            name='expenses',
            field=models.ManyToManyField(help_text='Expenses under this Expense Group', to='fyle.expense'),
        ),
        migrations.AddField(
            model_name='accountingexport',
            name='workspace',
            field=models.ForeignKey(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, to='workspaces.workspace'),
        ),
    ]
