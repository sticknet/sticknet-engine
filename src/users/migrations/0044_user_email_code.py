# Generated by Django 3.1.5 on 2023-09-03 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0043_preferences_photo_backup_setting'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
