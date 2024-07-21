# Generated by Django 3.1.5 on 2024-02-07 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0062_auto_20240207_0846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='color',
            field=models.CharField(blank=True, choices=[('rgb(255,0,0)', 'red'), ('rgb(0,0,255)', 'blue'), ('rgb(0,128,0)', 'green'), ('rgb(255,165,0)', 'orange'), ('rgb(128,0,128)', 'purple'), ('rgb(50,205,50)', 'limegreen'), ('rgb(255,20,147)', 'deeppink'), ('rgb(139,0,0)', 'darkred'), ('rgb(0,191,255)', 'deepskyblue'), ('rgb(147,112,219)', 'mediumpurple')], max_length=20, null=True),
        ),
    ]
