# Generated by Django 3.1.7 on 2021-04-05 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_basket_no_delivery_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='cover_format',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='publish_date',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]