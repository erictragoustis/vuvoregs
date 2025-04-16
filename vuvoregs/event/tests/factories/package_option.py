# tests/factories/package_option.py
import factory
import json
from faker import Faker
from event.models import PackageOption
from event.tests.factories.race_package import RacePackageFactory

fake = Faker()


class PackageOptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PackageOption

    package = factory.SubFactory(RacePackageFactory)
    name = factory.LazyAttribute(lambda _: fake.word().capitalize())
    values = factory.LazyAttribute(
        lambda _: json.dumps([fake.color_name() for _ in range(3)])
    )
