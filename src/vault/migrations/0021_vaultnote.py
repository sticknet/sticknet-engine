# Generated by Django 3.1.5 on 2023-09-02 07:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vault', '0020_auto_20230902_1043'),
    ]

    operations = [
        migrations.CreateModel(
            name='VaultNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=3000)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vault_notes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
