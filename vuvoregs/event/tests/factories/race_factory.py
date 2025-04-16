import factory
from decimal import Decimal
from event.models import Race, RaceType
from event.tests.factories.event_factory import EventFactory
from event.models import RaceRole


class RaceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceType
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Type {n}")
    min_participants = 1

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.add(role)
            self.save()  # ✅ manual save instead of relying on auto-save


class RaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Race

    name = factory.Sequence(lambda n: f"Race {n}")
    event = factory.SubFactory(EventFactory)
    race_type = factory.SubFactory(RaceTypeFactory)
    race_km = Decimal("5.0")
    base_price_individual = Decimal("20.00")
    base_price_team = Decimal("15.00")
    team_discount_threshold = 3


class RaceRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RaceRole

    name = factory.Sequence(lambda n: f"Role {n}")
