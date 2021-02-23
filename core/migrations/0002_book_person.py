# Generated by Django 3.1.7 on 2021-02-23 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=120)),
                ('last_name', models.CharField(blank=True, max_length=120, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1024)),
                ('description', models.TextField(blank=True, null=True)),
                ('isbn', models.CharField(blank=True, max_length=20, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('authors', models.ManyToManyField(related_name='authored_books', to='core.Person')),
                ('editors', models.ManyToManyField(blank=True, related_name='edited_books', to='core.Person')),
                ('translators', models.ManyToManyField(blank=True, related_name='translated_books', to='core.Person')),
            ],
        ),
    ]