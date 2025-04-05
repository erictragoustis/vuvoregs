from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
import json

from event.models import (
    Event, Race, RacePackage, PackageOption,
    PickUpPoint, TermsAndConditions, Athlete,
    Registration, RaceType
)


class Command(BaseCommand):
    help = "Seed the database with dummy events, races, packages, options, and athletes"

    def handle(self, *args, **kwargs):
        fake = Faker()
        total_athletes = 0

        # Seed race types if not already existing
        if RaceType.objects.count() == 0:
            for name in ["Fun Run", "Marathon", "Relay"]:
                RaceType.objects.create(name=name)

        # Clear existing event-related data
        Event.objects.all().delete()
        self.stdout.write(self.style.WARNING("🧹 Cleared old event-related data"))

        for e in range(8, 11):  # 8–10 events
            event = Event.objects.create(
                name=f"Marathon {2020 + e}",
                location=fake.city(),
                date=fake.date_between(start_date="+10d", end_date="+6M")
            )

            # Pickup points
            pickups = []
            for _ in range(random.randint(2, 4)):
                pickups.append(PickUpPoint.objects.create(
                    event=event,
                    name=fake.street_name(),
                    address=fake.address(),
                    working_hours="Mon–Fri 9am–5pm"
                ))

            # Terms
            terms = TermsAndConditions.objects.create(
                event=event,
                title=f"T&Cs for {event.name}",
                content="These are sample Terms & Conditions.",
                version="1.0"
            )

            for r in range(3):  # 3 races per event
                race = Race.objects.create(
                    event=event,
                    name=fake.word().capitalize() + f" Run {r + 1}",
                    race_km=random.choice([5, 10, 21]),
                    min_participants=1,
                    race_type=RaceType.objects.order_by("?").first()
                )

                packages = []
                for _ in range(random.randint(1, 2)):  # 1–3 packages
                    package = RacePackage.objects.create(
                        event=event,
                        name=fake.color_name() + " Package",
                        price=random.randint(10, 20),
                        description=fake.sentence()
                    )
                    package.races.add(race)
                    packages.append(package)

                    for _ in range(random.randint(1, 5)):  # 1–2 options
                        option_name = fake.word().capitalize() + " Option"
                        choices = [fake.word().capitalize() for _ in range(random.randint(3, 5))]
                        PackageOption.objects.create(
                            package=package,
                            name=option_name,
                            options_json=choices,
                            options_string=", ".join(choices)
                        )

                # Create athletes for this race
                for _ in range(random.randint(10, 15)):  # 10–15 per race
                    reg = Registration.objects.create(
                    event=event,
                    status="completed",
                    payment_status="paid",
                    total_amount=random.randint(20, 100)
                )

                    athlete = Athlete.objects.create(
                        registration=reg,
                        race=race,
                        package=random.choice(packages),
                        pickup_point=random.choice(pickups),
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        email=fake.unique.email(),
                        phone=fake.phone_number(),
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=55),
                        hometown=fake.city(),
                        agreed_to_terms=terms,
                        sex=random.choice(['Male', 'Female']),
                        agrees_to_terms=True,
                        selected_options={}
                    )

                    # Assign selected options
                    selected_options = {}
                    for po in PackageOption.objects.filter(package=athlete.package):
                        values = po.options_json
                        selected_options[po.name] = random.sample(values, k=random.randint(1, min(2, len(values))))
                    athlete.selected_options = selected_options
                    athlete.save()

                    total_athletes += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {Event.objects.count()} events, {total_athletes} athletes."))
