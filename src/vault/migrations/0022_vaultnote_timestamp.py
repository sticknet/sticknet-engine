# Generated by Django 3.1.5 on 2023-09-02 07:28

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0021_vaultnote'),
    ]

    operations = [
        migrations.AddField(
            model_name='vaultnote',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
