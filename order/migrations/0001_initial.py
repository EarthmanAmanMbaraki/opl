# Generated by Django 4.0.2 on 2022-04-25 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('depot', '0001_initial'),
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_no', models.CharField(blank=True, max_length=50, null=True)),
                ('order_no', models.CharField(max_length=50)),
                ('date', models.DateField()),
                ('vol_obs', models.FloatField()),
                ('vol_20', models.FloatField()),
                ('selling_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('is_loaded', models.BooleanField(default=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='depot.product')),
                ('truck', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='customer.truck')),
            ],
        ),
    ]