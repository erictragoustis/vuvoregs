# tests/factories/terms.py
import factory
from event.models import TermsAndConditions
from tests.factories.event import EventFactory


class TermsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TermsAndConditions

    event = factory.SubFactory(EventFactory)
    title = factory.Sequence(lambda n: f"Terms {n}")
    content = "Sample Terms and Conditions"
    version = "1.0"
