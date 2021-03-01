# Generated by Django 3.1.7 on 2021-02-28 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_userprofilephoneverification'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='cover_type',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='page_count',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]