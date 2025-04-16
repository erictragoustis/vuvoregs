from django.utils.timezone import now, timedelta
import pytest

from event.tests.factories.athlete_factory import AthleteFactory
from event.tests.factories.event_factory import EventFactory
from event.tests.factories.race_factory import RaceFactory


@pytest.mark.django_db
def test_event_registration_open():
    event = EventFactory(
        date=now().date() + timedelta(days=10),
        registration_start_date=now() - timedelta(days=1),
        registration_end_date=now() + timedelta(days=1),
        is_available=True,
    )
    assert event.is_registration_open() is True


@pytest.mark.django_db
def test_event_registration_closed_due_to_date():
    event = EventFactory(
        date=now().date() - timedelta(days=1),
        registration_start_date=now() - timedelta(days=10),
        registration_end_date=now() + timedelta(days=1),
        is_available=True,
    )
    assert event.is_registration_open() is False


@pytest.mark.django_db
def test_event_slots_remaining_none_if_unlimited():
    event = EventFactory(max_participants=None)
    assert event.available_slots_remaining is None


@pytest.mark.django_db
def test_event_slots_remaining_calculation():
    event = EventFactory(max_participants=5)
    registration = RegistrationFactory(event=event, payment_status="paid")
    AthleteFactory.create_batch(
        3, registration=registration, race=RaceFactory(event=event)
    )
    event.paid_athletes  # trigger cached_property
    assert event.available_slots_remaining == 2


@pytest.mark.django_db
def test_get_paid_athletes_by_pickup_point():
    event = EventFactory()
    pickup = event.pickup_points.first()
    registration = RegistrationFactory(event=event, payment_status="paid")
    athlete = AthleteFactory(
        registration=registration, race=RaceFactory(event=event), pickup_point=pickup
    )
    result = event.get_paid_athletes_by_pickup_point()
    assert pickup in result
    assert athlete in result[pickup]
