# Generated by Django 3.1.5 on 2023-07-28 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0002_auto_20230727_2115'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
