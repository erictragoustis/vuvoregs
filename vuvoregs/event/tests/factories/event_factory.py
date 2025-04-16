# tests/factories/event_factory.py
import factory
from event.models import Event
from django.utils.timezone import now, timedelta


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Event {n}")
    date = factory.LazyFunction(lambda: now().date() + timedelta(days=30))
    location = "Athens"
    is_available = True
    registration_start_date = factory.LazyFunction(lambda: now() - timedelta(days=1))
    registration_end_date = factory.LazyFunction(lambda: now() + timedelta(days=10))
