# Generated by Django 3.1.5 on 2022-09-17 12:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0008_auto_20210718_1002'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cipher',
            old_name='fileSize',
            new_name='file_size',
        ),
        migrations.RenameField(
            model_name='groupcover',
            old_name='fileSize',
            new_name='file_size',
        ),
    ]
