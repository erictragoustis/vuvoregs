import factory
from event.models import Registration
from event.tests.factories.event_factory import EventFactory


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    event = factory.SubFactory(EventFactory)
