# Generated by Django 3.1.5 on 2022-07-12 13:46

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_user_backupfreq'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preferences',
            name='favoritesIds',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=10), blank=True, default=list, null=True, size=None),
        ),
    ]
