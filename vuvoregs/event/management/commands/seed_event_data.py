from datetime import datetime, timedelta
from decimal import Decimal
import json
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware, now
from faker import Faker

from event.models import (
    Athlete,
    Event,
    PackageOption,
    Payment,
    PickUpPoint,
    Race,
    RacePackage,
    RaceRole,
    RaceSpecialPrice,
    RaceType,
    Registration,
    TermsAndConditions,
    TimeBasedPrice,
)


class Command(BaseCommand):
    help = "Seed events, races, packages, and athletes with realistic data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Seed only 1 event and 5 athletes per race.",
        )

    def handle(self, *args, **options):
        debug = options["debug"]
        fake = Faker()
        User = get_user_model()

        self.stdout.write(self.style.WARNING("🧹 Clearing existing data..."))
        models_to_clear = [
            Athlete,
            Registration,
            Payment,
            PackageOption,
            RacePackage,
            Race,
            TermsAndConditions,
            PickUpPoint,
            Event,
            RaceSpecialPrice,
            TimeBasedPrice,
        ]
        for model in models_to_clear:
            model.objects.all().delete()

        # Create default race types & roles
        if RaceType.objects.count() == 0:
            runner = RaceRole.objects.get_or_create(name="Runner")[0]
            cyclist = RaceRole.objects.get_or_create(name="Cyclist")[0]
            RaceType.objects.create(name="Fun Run")
            rt = RaceType.objects.create(name="Duathlon", min_participants=2)
            rt.roles.set([runner, cyclist])

        staff_users = User.objects.filter(is_staff=True)
        if not staff_users.exists():
            self.stdout.write(self.style.ERROR("❌ No staff users found."))
            return

        event_count = 1 if debug else random.randint(2, 5)

        for _ in range(event_count):
            organizer = random.choice(staff_users)
            event = Event.objects.create(
                name=f"{fake.city()} Run {datetime.now().year}",
                location=fake.city(),
                date=fake.date_between(start_date="+10d", end_date="+60d"),
                organizer=organizer,
                is_available=True,
                registration_start_date=make_aware(datetime.now() - timedelta(days=60)),
                registration_end_date=make_aware(datetime.now() + timedelta(days=60)),
            )

            TermsAndConditions.objects.create(
                event=event, content="Standard race terms apply.", version="1.0"
            )

            pickup_points = [
                PickUpPoint.objects.create(
                    event=event,
                    name=fake.company(),
                    address=fake.address(),
                    working_hours="Mon–Fri 9am–5pm",
                )
                for _ in range(random.randint(2, 4))
            ]

            races = []
            for _ in range(random.randint(2, 5)):
                race_type = random.choice(RaceType.objects.all())
                race = Race.objects.create(
                    event=event,
                    name=f"{fake.word().capitalize()} Dash",
                    race_type=race_type,
                    race_km=random.choice([5.0, 10.0, 21.1]),
                    base_price_individual=random.randint(20, 40),
                    base_price_team=random.randint(15, 30),
                    team_discount_threshold=random.choice([None, 3, 5]),
                )
                races.append(race)

                # Time-based prices
                start = now()
                TimeBasedPrice.objects.create(
                    race=race,
                    label="Early Bird",
                    start_date=start - timedelta(days=10),
                    end_date=start + timedelta(days=10),
                    price_adjustment=Decimal("-5.00"),
                )
                TimeBasedPrice.objects.create(
                    race=race,
                    label="Late Fee",
                    start_date=start + timedelta(days=30),
                    end_date=start + timedelta(days=90),
                    price_adjustment=Decimal("5.00"),
                )

                # Special prices
                for _ in range(1):
                    RaceSpecialPrice.objects.create(
                        race=race,
                        name=fake.word().capitalize() + " Discount",
                        label="Local Citizen",
                        description="Discount for residents or students",
                        discount_amount=random.choice([5, 10]),
                    )

                # Packages
                for _ in range(random.randint(1, 3)):
                    pkg = RacePackage.objects.create(
                        event=event,
                        race=race,
                        name=fake.color_name() + " Package",
                        description="Includes bib and chip",
                        price_adjustment=random.choice([0, 5, 10]),
                    )

                    for _ in range(random.randint(1, 2)):
                        options = ["XS", "S", "M", "L", "XL"]
                        option = PackageOption.objects.create(
                            package=pkg,
                            name=fake.word().capitalize() + " Option",
                            options_string=", ".join(options),
                        )
                        option.set_options_from_string(option.options_string)

            # Registration & athletes
            for race in races:
                num_athletes = 5 if debug else random.randint(20, 40)
                created = 0
                while created < num_athletes:
                    reg = Registration.objects.create(
                        event=event,
                        status="completed",
                        payment_status="paid",
                        agreed_to_terms=event.terms,
                        agrees_to_terms=True,
                        created_at=make_aware(
                            fake.date_time_between(start_date="-60d", end_date="now")
                        ),
                    )

                    n = min(random.randint(1, 4), num_athletes - created)
                    for _ in range(n):
                        valid_packages = race.packages.all()
                        if not valid_packages.exists():
                            continue
                        pkg = random.choice(valid_packages)
                        options = {
                            opt.name: [random.choice(opt.options_json)]
                            for opt in pkg.packageoption_set.all()
                            if opt.options_json
                        }

                        role = None
                        if race.requires_roles():
                            allowed = race.get_allowed_roles()
                            role = random.choice(list(allowed)) if allowed else None

                        special_price = (
                            random.choice(list(race.special_prices.all()))
                            if race.special_prices.exists() and random.random() < 0.4
                            else None
                        )

                        Athlete.objects.create(
                            registration=reg,
                            race=race,
                            package=pkg,
                            pickup_point=random.choice(pickup_points),
                            first_name=fake.first_name(),
                            last_name=fake.last_name(),
                            team=fake.word().capitalize() + " Club",
                            email=fake.unique.email(),
                            phone=fake.phone_number(),
                            sex=random.choice(["Male", "Female"]),
                            dob=fake.date_of_birth(minimum_age=16, maximum_age=55),
                            hometown=fake.city(),
                            selected_options=options,
                            role=role,
                            special_price=special_price,
                        )

                    reg.update_total_amount()
                    Payment.objects.create(
                        variant="dummy",
                        total=Decimal(reg.total_amount),
                        currency="EUR",
                        description=f"Reg #{reg.id}",
                        billing_email=reg.athletes.first().email,
                        status="confirmed",
                        captured_amount=Decimal("0.00"),
                        extra_data=json.dumps({"registration_id": reg.id}),
                    )

                    created += n

        self.stdout.write(self.style.SUCCESS("✅ Dummy data successfully created."))
