# event/tests/factories/event_factory.py
import factory
from event.models import Event
from django.utils import timezone
from datetime import timedelta


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Faker("sentence", nb_words=3)
    date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    location = factory.Faker("city")
    description = factory.Faker("paragraph")
    email = factory.Faker("email")
    registration_start_date = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=1)
    )
    registration_end_date = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7)
    )
    is_available = True
