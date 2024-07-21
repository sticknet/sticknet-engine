import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
User = get_user_model()



class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username=os.environ['SUPER_USER_USERNAME']).exists():
            User.objects.create_superuser(os.environ['SUPER_USER_USERNAME'], os.environ['SUPER_USER_EMAIL'], os.environ['SUPER_USER_PASSWORD'])
