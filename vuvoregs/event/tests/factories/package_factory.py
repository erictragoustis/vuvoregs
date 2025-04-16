import factory
from decimal import Decimal
from event.models import RacePackage
from event.tests.factories.race_factory import RaceFactory


class RacePackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RacePackage

    name = factory.Sequence(lambda n: f"Package {n}")
    description = "Includes timing chip and T-shirt"
    race = factory.SubFactory(RaceFactory)
    event = factory.SelfAttribute("race.event")
    price_adjustment = Decimal("5.00")
