# Generated by Django 3.1.5 on 2023-08-30 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0018_file_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='created_at',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
