# Generated by Django 3.1.7 on 2021-02-25 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_basket_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basket',
            name='invoice',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='core.invoice'),
        ),
    ]
