# Generated by Django 3.1.5 on 2023-04-30 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iap', '0013_transaction_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
