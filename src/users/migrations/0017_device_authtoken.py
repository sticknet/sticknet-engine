# Generated by Django 3.1.5 on 2021-07-18 04:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0007_auto_20190111_0542'),
        ('users', '0016_user_passwordblocktime'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='authToken',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='knox.authtoken'),
        ),
    ]
