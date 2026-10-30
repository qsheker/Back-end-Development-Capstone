import os
from datetime import date
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from concert.models import Concert

class Command(BaseCommand):
    help = 'Add course demo concerts and optional administrator without replacing existing data.'
    def handle(self, *args, **options):
        for name, city, day in [('Djirection Live', 'London', 12), ('Summer Sessions', 'Paris', 18), ('World Tour Finale', 'New York', 25)]:
            Concert.objects.get_or_create(concert_name=name, defaults={'city': city, 'date': date(2030, 6, day), 'duration': 2})
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if username and password:
            user, created = get_user_model().objects.get_or_create(username=username, defaults={'is_staff': True, 'is_superuser': True})
            if created:
                user.set_password(password)
                user.save()
        self.stdout.write(self.style.SUCCESS('Demo concerts ready; existing records preserved.'))
