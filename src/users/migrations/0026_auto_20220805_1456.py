# Generated by Django 3.1.5 on 2022-08-05 10:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_auto_20220720_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preferences',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='preferences', to=settings.AUTH_USER_MODEL),
        ),
    ]
