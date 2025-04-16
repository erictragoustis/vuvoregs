from accounts.models import User
from django.utils import timezone
import factory
from factory.django import DjangoModelFactory

from event.models import Event, PickUpPoint


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password")


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Test Event {n}")
    date = factory.LazyFunction(
        lambda: timezone.now().date() + timezone.timedelta(days=30)
    )
    location = factory.Faker("city")
    description = factory.Faker("text")
    organizer = factory.SubFactory(UserFactory)
    email = factory.Faker("email")
    pickup_date = factory.LazyFunction(
        lambda: timezone.now().date() + timezone.timedelta(days=28)
    )
    max_participants = 100
    registration_start_date = factory.LazyFunction(
        lambda: timezone.now() - timezone.timedelta(days=5)
    )
    registration_end_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=25)
    )
    is_available = True


class PickUpPointFactory(DjangoModelFactory):
    class Meta:
        model = PickUpPoint

    event = factory.SubFactory(EventFactory)
    name = factory.Sequence(lambda n: f"Pickup Point {n}")
    address = factory.Faker("address")
    working_hours = "Mon–Fri 9am–5pm"
