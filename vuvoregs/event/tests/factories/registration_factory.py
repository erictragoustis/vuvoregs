# tests/factories/registration_factory.py
import factory
from factory.django import DjangoModelFactory
from event.models import Registration
from event.tests.factories import EventFactory


class RegistrationFactory(DjangoModelFactory):
    """Factory for creating Registration instances."""

    class Meta:
        model = Registration

    event = factory.SubFactory(EventFactory)
    status = "pending"
    payment_status = "not_paid"
    agrees_to_terms = True
    total_amount = 0.00
    agreed_to_terms = None
    payment = None
