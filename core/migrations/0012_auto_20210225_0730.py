# Generated by Django 3.1.7 on 2021-02-25 07:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20210225_0730'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1.0)]),
        ),
        migrations.AddField(
            model_name='item',
            name='price',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
