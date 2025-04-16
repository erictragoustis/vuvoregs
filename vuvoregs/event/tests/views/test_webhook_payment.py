import pytest
import json
from django.urls import reverse
from event.models import Registration
from event.tests.factories.registration import RegistrationFactory
from event.tests.factories.athlete import AthleteFactory
from event.tests.factories.race import RaceFactory


@pytest.mark.django_db
def test_viva_webhook_marks_registration_confirmed(client):
    """POSTing valid Viva webhook with known TransactionId should confirm payment."""
    race = RaceFactory()
    registration = RegistrationFactory(
        race=race, transaction_id="abc123", total_amount=50
    )
    AthleteFactory(registration=registration, race=race)

    webhook_data = {
        "EventType": "TransactionPaymentCompleted",
        "TransactionId": "abc123",
        "OrderCode": "irrelevant",
        "Amount": 50,
    }

    response = client.post(
        "/webhooks/viva/",
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    registration.refresh_from_db()
    assert response.status_code == 200
    assert (
        registration.payment.status == "confirmed"
        or registration.payment.is_confirmed()
    )


@pytest.mark.django_db
def test_viva_webhook_with_unknown_transaction_id(client):
    """Webhook with unknown TransactionId should not crash or confirm anything."""
    webhook_data = {
        "EventType": "TransactionPaymentCompleted",
        "TransactionId": "nonexistent",
        "Amount": 99,
    }

    response = client.post(
        "/webhooks/viva/",
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    assert response.status_code in [
        200,
        204,
    ]  # Silent accept, or 404 depending on your view
