import factory
from event.models import RacePackage
from .event_factory import EventFactory
from .race_factory import RaceFactory


class RacePackageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RacePackage

    name = factory.Faker("color_name")
    event = factory.SubFactory(EventFactory)
    race = factory.SubFactory(RaceFactory)
    price_adjustment = 5.00
