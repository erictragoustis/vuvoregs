# tests/factories/race.py
import factory
from event.models import Race, RaceType
from tests.factories.event import EventFactory


class RaceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceType

    name = factory.Sequence(lambda n: f"Type {n}")


class RaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Race

    name = factory.Sequence(lambda n: f"Race {n}")
    race_km = factory.Iterator([5, 10, 21])
    event = factory.SubFactory(EventFactory)
    race_type = factory.SubFactory(RaceTypeFactory)
    min_participants = 1
