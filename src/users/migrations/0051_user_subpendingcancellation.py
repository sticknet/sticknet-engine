# Generated by Django 3.1.5 on 2023-10-21 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0050_auto_20230906_0947'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subPendingCancellation',
            field=models.BooleanField(default=False),
        ),
    ]
