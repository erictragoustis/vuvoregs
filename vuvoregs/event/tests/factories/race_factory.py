import factory

from event.models import Race
from event.models.race import RaceType

from .event_factory import EventFactory


class RaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Race

    event = factory.SubFactory(EventFactory)
    name = factory.Faker("word")
    race_km = 10
    race_type = factory.Iterator(RaceType.objects.all())  # or define RaceTypeFactory
    base_price_individual = 20
    base_price_team = 15
