import factory
from factory import SubFactory
from factory.fuzzy import FuzzyDecimal, FuzzyInteger
from datetime import timedelta

from django.utils.timezone import now

from event.models import Race, RaceType, RaceRole, TimeBasedPrice
from .event_factory import EventFactory


class RaceRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceRole

    name = factory.Faker("word")


class RaceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceType

    name = factory.Faker("word")
    description = factory.Faker("sentence")
    min_participants = FuzzyInteger(1, 5)

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.add(role)
        else:
            self.roles.add(RaceRoleFactory())


class RaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Race

    name = factory.Faker("sentence", nb_words=3)
    event = SubFactory(EventFactory)
    race_type = SubFactory(RaceTypeFactory)
    race_km = FuzzyDecimal(5.0, 42.0)
    base_price_individual = FuzzyDecimal(5.00, 50.00)
    base_price_team = FuzzyDecimal(3.00, 40.00)
    team_discount_threshold = FuzzyInteger(3, 10)
    max_participants = FuzzyInteger(100, 500)


class TimeBasedPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeBasedPrice

    race = SubFactory(RaceFactory)
    label = factory.Faker("catch_phrase")
    start_date = factory.LazyFunction(lambda: now() - timedelta(days=1))
    end_date = factory.LazyFunction(lambda: now() + timedelta(days=1))
    price_adjustment = FuzzyDecimal(-5.00, 10.00)
