import pytest
from django.urls import reverse
from django.utils import translation
from event.models import Payment
from event.tests.factories.registration_factory import RegistrationFactory
from event.tests.factories.payment_factory import PaymentFactory


@pytest.mark.django_db
def test_viva_webhook_updates_payment_status(client):
    """Should update payment status via webhook (matching by order_code)."""

    registration = RegistrationFactory()
    payment = PaymentFactory(
        status="waiting",
        order_code="ORD123",
        transaction_id="TEMP123",  # prevent IntegrityError
        set_registration=registration,
    )

    url = reverse("payment_webhook")
    payload = {
        "EventTypeId": 1796,  # Viva sends this for completed payment events
        "EventData": {
            "TransactionId": "TX123",  # Will be saved to payment
            "OrderCode": "ORD123",  # Used to find the correct payment
        },
    }

    # Force correct language prefix if i18n is enabled
    with translation.override("en"):
        response = client.post(url, data=payload, content_type="application/json")

    payment.refresh_from_db()
    assert response.status_code == 200
    assert payment.transaction_id == "TX123"
    assert payment.status == "confirmed"  # or "paid" based on your system logic
