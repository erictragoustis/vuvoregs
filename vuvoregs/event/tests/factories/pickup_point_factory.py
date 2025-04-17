import factory
from event.models.event import PickUpPoint
from event.tests.factories.event_factory import EventFactory


class PickupPointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PickUpPoint

    event = factory.SubFactory(EventFactory)
    name = factory.Faker("city")
    address = factory.Faker("address")
    working_hours = "Mon–Fri 9am–5pm"
