# Generated by Django 3.1.5 on 2023-09-24 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0023_auto_20230914_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='height',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='file',
            name='width',
            field=models.IntegerField(default=0),
        ),
    ]
