# Generated by Django 3.1.5 on 2023-12-13 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iap', '0019_auto_20231205_0850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='original_transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
