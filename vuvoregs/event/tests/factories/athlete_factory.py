import factory
from decimal import Decimal
from event.models import Athlete, RaceSpecialPrice
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.package_factory import RacePackageFactory
from event.tests.factories.event_factory import EventFactory


class RaceSpecialPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceSpecialPrice

    race = factory.SubFactory(RaceFactory)
    name = "Student Discount"
    label = "Student"
    discount_amount = Decimal("5.00")


class AthleteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Athlete

    race = factory.SubFactory(RaceFactory)
    package = factory.SubFactory(
        RacePackageFactory, race=factory.SelfAttribute("..race")
    )
    registration = factory.SubFactory(
        "event.tests.factories.registration_factory.RegistrationFactory",
        event=factory.SelfAttribute("..race.event"),
    )
    first_name = "John"
    last_name = "Doe"
    email = "john@example.com"
    phone = "1234567890"
    sex = "Male"
    hometown = "Athens"
