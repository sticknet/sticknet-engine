# Generated by Django 3.1.5 on 2023-08-17 06:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vault', '0009_file_previewcipher'),
    ]

    operations = [
        migrations.RenameField(
            model_name='file',
            old_name='previewCipher',
            new_name='preview_cipher',
        ),
    ]
