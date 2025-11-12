from django.core.management.base import BaseCommand
from listings.models import Listing
from django.contrib.auth.models import User
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Seed the database with sample listings'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create host user if none exists
        host, created = User.objects.get_or_create(username='host1')
        if created:
            host.set_password('password123')
            host.save()

        # Create 10 sample listings
        for _ in range(10):
            listing = Listing.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.text(max_nb_chars=200),
                location=fake.city(),
                price_per_night=random.randint(50, 500),
                host=host
            )
            self.stdout.write(self.style.SUCCESS(f'Created listing: {listing.title}'))
