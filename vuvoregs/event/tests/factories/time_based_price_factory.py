import factory
from datetime import timedelta
from decimal import Decimal
from django.utils.timezone import now
from event.models import TimeBasedPrice
from event.tests.factories.race_factory import RaceFactory


class TimeBasedPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeBasedPrice

    race = factory.SubFactory(RaceFactory)
    label = "Early Bird"
    price_adjustment = Decimal("5.00")
    start_date = factory.LazyFunction(lambda: now() - timedelta(days=1))
    end_date = factory.LazyFunction(lambda: now() + timedelta(days=1))
