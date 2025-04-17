import factory
from event.models import TermsAndConditions
from event.tests.factories.event_factory import EventFactory


class TermsAndConditionsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TermsAndConditions

    event = factory.SubFactory(EventFactory)
    version = "1.0"
    title = "Sample Terms"
    content = "These are the sample terms and conditions."
