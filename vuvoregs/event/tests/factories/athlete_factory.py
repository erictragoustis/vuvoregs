# tests/factories/athlete_factory.py
import factory
from factory.django import DjangoModelFactory

from event.models import Athlete
from event.tests.factories.race_package_factory import (
    PackageOptionFactory,
    RacePackageFactory,
)
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.registration_factory import RegistrationFactory
from event.tests.factories.event_factory import PickUpPointFactory


class AthleteFactory(DjangoModelFactory):
    """Factory for generating Athlete instances with dynamic options."""

    class Meta:
        model = Athlete

    registration = factory.SubFactory(RegistrationFactory)
    race = factory.SubFactory(RaceFactory)
    package = factory.SubFactory(RacePackageFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    fathers_name = factory.Faker("first_name")
    team = factory.Faker("word")
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    sex = factory.Iterator(["Male", "Female"])
    dob = factory.Faker("date_of_birth", minimum_age=10, maximum_age=60)
    hometown = factory.Faker("city")
    pickup_point = factory.SubFactory(PickUpPointFactory)
    special_price = None
    bib_number = factory.Faker("bothify", text="##??")

    @factory.lazy_attribute
    def selected_options(self):
        if not self.package.packageoption_set.exists():
            PackageOptionFactory.create_batch(2, package=self.package)

        options = {}
        for opt in self.package.packageoption_set.all():
            if opt.options_json:
                options[opt.name] = [opt.options_json[0]]
        return options
