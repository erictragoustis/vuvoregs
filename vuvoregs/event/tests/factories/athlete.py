# tests/factories/athlete.py
import factory
import json
from faker import Faker
from event.models import Athlete
from event.tests.factories.registration import RegistrationFactory
from event.tests.factories.race_package import RacePackageFactory
from event.tests.factories.event import PickUpPointFactory
from event.tests.factories.terms import TermsFactory

fake = Faker()


class AthleteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Athlete

    registration = factory.SubFactory(RegistrationFactory)
    race = factory.SelfAttribute("registration.race")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    phone = factory.Faker("phone_number")
    dob = factory.Faker("date_of_birth", minimum_age=18, maximum_age=55)
    hometown = factory.Faker("city")
    package = factory.SubFactory(
        RacePackageFactory, race=factory.SelfAttribute("..race")
    )
    pickup_point = factory.SubFactory(
        PickUpPointFactory, event=factory.SelfAttribute("..race.event")
    )
    agreed_to_terms = factory.SubFactory(
        TermsFactory, event=factory.SelfAttribute("..race.event")
    )
    agreed_at = factory.Faker("date_time_this_year")

    @factory.lazy_attribute
    def selected_options(self):
        return {"Size": ["M"], "Color": ["Red"]}
