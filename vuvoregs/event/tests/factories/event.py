# tests/factories/event.py
import factory
from faker import Faker
from event.models import Event, PickUpPoint

fake = Faker()


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Test Event {n}")
    location = factory.LazyAttribute(lambda _: fake.city())
    date = factory.Faker("future_date")


class PickUpPointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PickUpPoint

    event = factory.SubFactory(EventFactory)
    name = factory.LazyAttribute(lambda _: fake.street_name())
