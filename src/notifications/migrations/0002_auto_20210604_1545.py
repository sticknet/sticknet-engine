# Generated by Django 3.1.5 on 2021-06-04 11:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('notifications', '0001_initial'),
        ('photos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0002_auto_20210604_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='pntoken',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pn_tokens', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notification',
            name='album',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='photos.album'),
        ),
        migrations.AddField(
            model_name='notification',
            name='from_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications_sent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notification',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.group'),
        ),
        migrations.AddField(
            model_name='notification',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification', to='photos.image'),
        ),
        migrations.AddField(
            model_name='notification',
            name='note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='photos.note'),
        ),
        migrations.AddField(
            model_name='notification',
            name='sharedPhotos',
            field=models.ManyToManyField(blank=True, related_name='share_notification', to='photos.Image'),
        ),
        migrations.AddField(
            model_name='notification',
            name='to_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invitation',
            name='display_name',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitation_display_names', to='groups.cipher'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='from_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations_sent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invitation',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.group'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='to_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='from_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests_sent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='connectionrequest',
            name='to_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connection_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
