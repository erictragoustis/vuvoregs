"""Management command to seed the database with mock event.

Race, and athlete registration data.
"""

# Standard library imports
from datetime import datetime, timedelta
from decimal import Decimal
import json
import random

# Django imports
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

# Third-party imports
from faker import Faker

# Local app imports
from event.models import (
    Athlete,
    Event,
    PackageOption,
    Payment,
    PickUpPoint,
    Race,
    RacePackage,
    RaceType,
    Registration,
    TermsAndConditions,
)


class Command(BaseCommand):
    help = "Seed events, races, packages, and athletes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Seed only one event and five athletes per race",
        )

    def handle(self, *args, **kwargs):
        debug_mode = kwargs.get("debug", False)
        fake = Faker()
        User = get_user_model()

        # 🧹 Clear all relevant data
        self.stdout.write(self.style.WARNING("Clearing previous data..."))
        Payment.objects.all().delete()
        Athlete.objects.all().delete()
        Registration.objects.all().delete()
        PackageOption.objects.all().delete()
        RacePackage.objects.all().delete()
        Race.objects.all().delete()
        TermsAndConditions.objects.all().delete()
        PickUpPoint.objects.all().delete()
        Event.objects.all().delete()

        if RaceType.objects.count() == 0:
            for name in ["Fun Run", "Marathon", "Relay"]:
                RaceType.objects.create(name=name)

        staff_users = list(User.objects.filter(is_staff=True))
        if not staff_users:
            self.stdout.write(self.style.ERROR("No staff users found."))
            return

        event_count = 1 if debug_mode else random.randint(2, 6)

        for _ in range(event_count):
            organizer = random.choice(staff_users)
            event = Event.objects.create(
                name=f"{fake.city()} Marathon {datetime.now().year}",
                location=fake.city(),
                date=fake.date_between(start_date="+1d", end_date="+6M"),
                organizer=organizer,
                is_available=True,
                registration_start_date=make_aware(datetime.now()),
                registration_end_date=make_aware(datetime.now() + timedelta(days=90)),
            )

            pickups = [
                PickUpPoint.objects.create(
                    event=event,
                    name=fake.company(),
                    address=fake.address(),
                    working_hours="Mon–Fri 9am–5pm",
                )
                for _ in range(random.randint(2, 4))
            ]

            terms = TermsAndConditions.objects.create(
                event=event,
                title=f"T&Cs for {event.name}",
                content="Sample terms.",
                version="1.0",
            )

            races = [
                Race.objects.create(
                    event=event,
                    name=f"{fake.word().capitalize()} Sprint",
                    race_km=random.choice([5, 10, 21]),
                    min_participants=random.randint(1, 3),
                    race_type=RaceType.objects.order_by("?").first(),
                )
                for _ in range(random.randint(1, 6))
            ]

            packages = []
            assigned_races = set()
            for _ in range(random.randint(1, 3)):
                package = RacePackage.objects.create(
                    event=event,
                    name=fake.color_name() + " Package",
                    price=random.randint(20, 120),
                    description=fake.sentence(),
                )
                assigned_to = random.sample(
                    races, k=random.randint(1, min(3, len(races)))
                )
                package.races.set(assigned_to)
                assigned_races.update(r.id for r in assigned_to)
                packages.append(package)

                for _ in range(random.randint(1, 3)):
                    choices = [
                        fake.word().capitalize() for _ in range(random.randint(3, 5))
                    ]
                    PackageOption.objects.create(
                        package=package,
                        name=fake.word().capitalize() + " Option",
                        options_json=choices,
                        options_string=", ".join(choices),
                    )

            # 🔁 Ensure all races have at least one package assigned
            for race in races:
                if race.id not in assigned_races:
                    random.choice(packages).races.add(race)
                    assigned_races.add(race.id)

            for race_index, race in enumerate(races):
                self.stdout.write(
                    f"→ Creating athletes for race {race_index + 1}/{len(races)}: {race.name}"
                )  # noqa: E501
                athletes_needed = 5 if debug_mode else random.randint(20, 40)
                created = 0

                while created < athletes_needed:
                    num_athletes = min(random.randint(1, 4), athletes_needed - created)

                    registration = Registration.objects.create(
                        event=event,
                        status="completed",
                        payment_status="paid",
                        total_amount=0.00,
                    )
                    registration.created_at = make_aware(
                        fake.date_time_between(start_date="-120d", end_date="now")
                    )
                    registration.save(update_fields=["created_at"])

                    for _ in range(num_athletes):
                        valid_packages = [p for p in packages if race in p.races.all()]
                        if not valid_packages:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️ No valid packages for race: {race.name}"
                                )
                            )
                            break

                        chosen_package = random.choice(valid_packages)
                        selected_options = {
                            opt.name: [random.choice(opt.options_json)]
                            for opt in chosen_package.packageoption_set.all()
                            if opt.options_json
                        }

                        athlete = Athlete.objects.create(
                            registration=registration,
                            race=race,
                            package=chosen_package,
                            pickup_point=random.choice(pickups),
                            first_name=fake.first_name(),
                            last_name=fake.last_name(),
                            team=fake.word().capitalize() + " Runners",
                            email=fake.unique.email(),
                            phone=fake.phone_number(),
                            sex=random.choice(["Male", "Female"]),
                            dob=fake.date_of_birth(minimum_age=18, maximum_age=55),
                            hometown=fake.city(),
                            agreed_to_terms=terms,
                            agrees_to_terms=True,
                            selected_options=selected_options,
                        )

                        registration.total_amount += float(chosen_package.price)
                        created += 1

                    registration.save(update_fields=["total_amount"])

                    payment = Payment.objects.create(
                        variant="dummy",
                        description=f"Registration #{registration.id}",
                        total=Decimal(registration.total_amount),
                        currency="EUR",
                        billing_email=registration.athletes.first().email
                        if registration.athletes.exists()
                        else fake.email(),
                        status="confirmed",
                        captured_amount=Decimal("0.00"),
                        extra_data=json.dumps({"registration_id": registration.id}),
                    )
                    registration.payment = payment
                    registration.save()

        self.stdout.write(self.style.SUCCESS("✅ Seeder completed successfully."))
