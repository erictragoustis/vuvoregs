# tests/factories/package.py

import factory
from factory.django import DjangoModelFactory
from event.models.package import PackageOption, RaceSpecialPrice
from event.models.package import RacePackage  # Ensure this is already in your factories

from .race_factory import RaceFactory


class RacePackageFactory(DjangoModelFactory):
    class Meta:
        model = RacePackage

    event = factory.SubFactory("event.tests.factories.EventFactory")
    race = factory.SubFactory(RaceFactory)
    name = factory.Sequence(lambda n: f"Package {n}")
    description = factory.Faker("sentence")
    price_adjustment = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True
    )


class PackageOptionFactory(DjangoModelFactory):
    class Meta:
        model = PackageOption

    package = factory.SubFactory(RacePackageFactory)
    name = factory.Sequence(lambda n: f"Option {n}")
    options_json = factory.LazyFunction(lambda: ["S", "M", "L", "XL"])
    options_string = "S, M, L, XL"


class RaceSpecialPriceFactory(DjangoModelFactory):
    class Meta:
        model = RaceSpecialPrice

    race = factory.SubFactory(RaceFactory)
    name = factory.Sequence(lambda n: f"Special {n}")
    label = factory.Faker("word")
    description = factory.Faker("sentence")
    discount_amount = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, positive=True
    )
