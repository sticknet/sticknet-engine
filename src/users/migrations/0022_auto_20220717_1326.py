# Generated by Django 3.1.5 on 2022-07-17 09:26

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_auto_20220714_1649'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='hiddenImages',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=list, null=True, size=None),
        ),
    ]
