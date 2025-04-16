# tests/factories/registration.py
import factory
from event.models import Registration
from event.tests.factories.race import RaceFactory


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    race = factory.SubFactory(RaceFactory)
