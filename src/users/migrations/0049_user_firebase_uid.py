# Generated by Django 3.1.5 on 2023-09-04 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0048_auto_20230903_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='firebase_uid',
            field=models.CharField(blank=True, max_length=56, null=True),
        ),
    ]
