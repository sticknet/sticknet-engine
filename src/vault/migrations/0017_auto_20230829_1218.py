# Generated by Django 3.1.5 on 2023-08-29 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0016_auto_20230829_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='folder_type',
            field=models.CharField(blank=True, choices=[('normal', 'Normal'), ('home', 'Home'), ('camera_uploads', 'Camera Uploads')], max_length=20, null=True),
        ),
    ]
