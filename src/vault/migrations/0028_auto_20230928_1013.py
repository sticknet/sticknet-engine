# Generated by Django 3.1.5 on 2023-09-28 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0027_auto_20230928_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='type',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
