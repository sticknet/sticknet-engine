# Generated by Django 3.1.5 on 2021-07-03 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0005_auto_20210618_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='cipher',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='groupcover',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
