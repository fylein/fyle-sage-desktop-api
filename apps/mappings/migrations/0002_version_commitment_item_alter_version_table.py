# Generated by Django 4.1.2 on 2024-02-01 10:41

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mappings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='commitment_item',
            field=sage_desktop_api.models.fields.IntegerNullField(help_text='version for commitment item', null=True),
        ),
        migrations.AlterModelTable(
            name='version',
            table='versions',
        ),
    ]
