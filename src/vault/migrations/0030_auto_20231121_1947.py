# Generated by Django 3.1.5 on 2023-11-21 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0029_auto_20231105_1550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
