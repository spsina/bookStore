# Generated by Django 3.1.7 on 2021-02-25 07:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20210225_0730'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='create_datetime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]