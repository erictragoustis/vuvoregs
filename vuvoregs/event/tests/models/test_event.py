import pytest
from datetime import timedelta
from django.utils.timezone import now
from event.models import Event
from event.tests.factories.event_factory import EventFactory


@pytest.mark.django_db
def test_registration_open_returns_true():
    """It should return True if the event is currently open for registration."""
    event = EventFactory(
        registration_start_date=now() - timedelta(days=1),
        registration_end_date=now() + timedelta(days=10),
        date=now().date() + timedelta(days=5),
        is_available=True,
    )

    assert event.is_registration_open() is True


@pytest.mark.django_db
def test_registration_closed_if_date_passed():
    """It should return False if the event date has passed."""
    event = EventFactory(date=now().date() - timedelta(days=1))

    assert event.is_registration_open() is False
