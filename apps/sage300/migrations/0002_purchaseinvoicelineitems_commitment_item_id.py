# Generated by Django 4.1.2 on 2024-02-01 20:23

from django.db import migrations
import sage_desktop_api.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sage300', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseinvoicelineitems',
            name='commitment_item_id',
            field=sage_desktop_api.models.fields.StringNullField(help_text='destination id of commitment item', max_length=255, null=True),
        ),
    ]