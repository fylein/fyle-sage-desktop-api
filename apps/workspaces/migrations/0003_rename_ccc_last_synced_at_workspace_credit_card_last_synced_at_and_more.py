# Generated by Django 4.1.2 on 2023-11-20 10:58

from django.db import migrations, models
import django.db.models.deletion
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0002_sage300credential_importsetting_fylecredential_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workspace',
            old_name='ccc_last_synced_at',
            new_name='credit_card_last_synced_at',
        ),
        migrations.RenameField(
            model_name='workspace',
            old_name='last_synced_at',
            new_name='reimbursable_last_synced_at',
        ),
        migrations.RemoveField(
            model_name='advancedsetting',
            name='schedule_id',
        ),
        migrations.AddField(
            model_name='advancedsetting',
            name='schedule',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='django_q.schedule'),
        ),
        migrations.AddField(
            model_name='advancedsetting',
            name='sync_sage_300_to_fyle_payments',
            field=sage_desktop_api.models.fields.BooleanFalseField(default=False, help_text='Sync sage 300 to fyle payments'),
        ),
        migrations.AlterField(
            model_name='importsetting',
            name='workspace',
            field=models.OneToOneField(help_text='Reference to Workspace model', on_delete=django.db.models.deletion.PROTECT, related_name='import_settings', to='workspaces.workspace'),
        ),
    ]
