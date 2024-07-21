# Generated by Django 3.1.5 on 2023-09-06 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0049_user_firebase_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='country',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='dial_code',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
