import factory
from event.models import Registration
from .event_factory import EventFactory


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    event = factory.SubFactory(EventFactory)
    agrees_to_terms = True
