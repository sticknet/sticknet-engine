# Generated by Django 3.1.5 on 2021-06-24 08:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0006_auto_20210624_1222'),
    ]

    operations = [
        migrations.RenameField(
            model_name='error',
            old_name='route',
            new_name='screen',
        ),
    ]
