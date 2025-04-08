from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
import json
from django.utils.timezone import make_aware  

from django.contrib.auth import get_user_model
from event.models import (
    Event, Race, RacePackage, PackageOption, PickUpPoint,
    TermsAndConditions, Athlete, Registration, RaceType
)


class Command(BaseCommand):
    help = "Seed the database with random events, races, packages, options, and athletes with multi-registration support"

    def handle(self, *args, **kwargs):
        fake = Faker()
        total_athletes = 0

        # 🧹 Clear old data
        Event.objects.all().delete()
        self.stdout.write(self.style.WARNING("🧹 Cleared old event-related data"))

        # Seed RaceTypes
        if RaceType.objects.count() == 0:
            for name in ["Fun Run", "Marathon", "Relay"]:
                RaceType.objects.create(name=name)

        User = get_user_model()
        staff_users = list(User.objects.filter(is_staff=True))
        if not staff_users:
            self.stdout.write(self.style.ERROR("❌ No staff users found. Cannot assign organizers."))
            return

        event_count = random.randint(2, 6)

        for e in range(event_count):
            organizer = random.choice(staff_users)
            event = Event.objects.create(
                name=f"{fake.city()} Marathon {2025 + e}",
                location=fake.city(),
                date=fake.date_between(start_date="+1d", end_date="+6M"),
                organizer=organizer,
                is_available=True,
                registration_start_date=timezone.now(),
                registration_end_date=timezone.now() + timezone.timedelta(days=90)
            )

            pickups = []
            for _ in range(random.randint(2, 4)):
                pickups.append(PickUpPoint.objects.create(
                    event=event,
                    name=fake.company(),
                    address=fake.address(),
                    working_hours="Mon–Fri 9am–5pm"
                ))

            terms = TermsAndConditions.objects.create(
                event=event,
                title=f"T&Cs for {event.name}",
                content="These are the event participation rules.",
                version="1.0"
            )

            races = []
            for _ in range(random.randint(1, 6)):
                race = Race.objects.create(
                    event=event,
                    name=f"{fake.word().capitalize()} Sprint",
                    race_km=random.choice([5, 10, 21]),
                    min_participants=1,
                    race_type=RaceType.objects.order_by("?").first()
                )
                races.append(race)

            packages = []
            for _ in range(random.randint(1, 3)):
                package = RacePackage.objects.create(
                    event=event,
                    name=fake.color_name() + " Package",
                    price=random.randint(20, 120),
                    description=fake.sentence()
                )
                for race in random.sample(races, k=random.randint(1, min(3, len(races)))):
                    package.races.add(race)
                packages.append(package)

                for _ in range(random.randint(2, 7)):
                    choices = [fake.word().capitalize() for _ in range(random.randint(3, 5))]
                    PackageOption.objects.create(
                        package=package,
                        name=fake.word().capitalize() + " Option",
                        options_json=choices,
                        options_string=", ".join(choices)
                    )

            athlete_target = random.randint(50, 400)
            athletes_created = 0

            while athletes_created < athlete_target:
                race = random.choice(races)

                registration = Registration.objects.create(
                    event=event,
                    status='completed',
                    payment_status='paid',
                    total_amount=0.00
                )

                # Override created_at
                registration.created_at = make_aware(fake.date_time_between(start_date='-120d', end_date='now'))
                registration.save(update_fields=['created_at'])

                num_athletes = min(random.randint(1, 4), athlete_target - athletes_created)

                for _ in range(num_athletes):
                    package_choices = [p for p in packages if race in p.races.all()]
                    if not package_choices:
                        continue

                    chosen_package = random.choice(package_choices)

                    athlete = Athlete.objects.create(
                        registration=registration,
                        race=race,
                        package=chosen_package,
                        pickup_point=random.choice(pickups),
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        email=fake.unique.email(),
                        phone=fake.phone_number(),
                        sex=random.choice(['Male', 'Female']),
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=55),
                        hometown=fake.city(),
                        agreed_to_terms=terms,
                        agrees_to_terms=True,
                    )

                    selected_options = {}
                    for opt in PackageOption.objects.filter(package=chosen_package):
                        if opt.options_json:
                            selected_options[opt.name] = [random.choice(opt.options_json)]
                    athlete.selected_options = selected_options
                    athlete.save()

                    registration.total_amount += float(chosen_package.price)
                    athletes_created += 1

                registration.save(update_fields=['total_amount'])

        self.stdout.write(self.style.SUCCESS(
            f"✅ Created {event_count} events with {total_athletes + athletes_created} total athletes."
        ))
