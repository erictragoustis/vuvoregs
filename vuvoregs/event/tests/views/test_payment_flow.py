import pytest
from django.urls import reverse
from event.models import Registration, Athlete
from event.tests.factories.race import RaceFactory
from event.tests.factories.registration import RegistrationFactory
from event.tests.factories.athlete import AthleteFactory


@pytest.mark.django_db
def test_payment_success_view_marks_registration_paid(client):
    """GET to payment success URL with valid transaction ID should mark paid."""
    race = RaceFactory()
    registration = RegistrationFactory(race=race)
    registration.transaction_id = "12345"
    registration.total_amount = 50
    registration.save()

    AthleteFactory(registration=registration, race=race)

    url = reverse("payments:success")
    response = client.get(f"{url}?t=12345")

    registration.refresh_from_db()
    assert response.status_code == 200
    assert (
        registration.payment.status == "confirmed"
        or registration.payment.is_confirmed()
    )
    assert b"Thank you" in response.content or b"success" in response.content.lower()


@pytest.mark.django_db
def test_payment_failure_view_does_not_confirm(client):
    """GET to payment failure view should not confirm payment."""
    registration = RegistrationFactory(transaction_id="fail123", total_amount=40)

    url = reverse("payments:failure")
    response = client.get(f"{url}?t=fail123")

    registration.refresh_from_db()
    assert response.status_code == 200
    assert not registration.payment.is_confirmed()
    assert b"fail" in response.content.lower() or b"problem" in response.content.lower()
