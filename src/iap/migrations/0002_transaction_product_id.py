# Generated by Django 3.1.5 on 2023-03-19 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='product_id',
            field=models.CharField(choices=[('com.stiiick.premium.1', 'sqaure'), ('com.stiiick.premium.2', 'circle'), ('com.stiiick.premium.3', 'triangle')], default='com.stiiick.premium.1', max_length=100),
        ),
    ]
