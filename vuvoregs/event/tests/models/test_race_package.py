# tests/factories/race_package.py
import factory
from event.models import RacePackage
from event.tests.factories.race import RaceFactory


class RacePackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RacePackage

    race = factory.SubFactory(RaceFactory)
    name = factory.Sequence(lambda n: f"Package {n}")
    price = factory.Iterator([25, 50, 75])
