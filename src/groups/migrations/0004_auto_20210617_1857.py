# Generated by Django 3.1.5 on 2021-06-17 14:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0003_auto_20210613_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='group_owner', to=settings.AUTH_USER_MODEL),
        ),
    ]
