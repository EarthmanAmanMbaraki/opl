# Generated by Django 4.0.2 on 2022-05-06 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_alter_entry_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='vol_20',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
