import json

from django.http import JsonResponse
from django.urls import reverse
from django.utils import translation
import pytest

from event.models import Payment
from event.tests.factories import RegistrationFactory, PaymentFactory


@pytest.mark.django_db
def test_webhook_payment_not_found(client):
    """Should return 404 if OrderCode doesn't match any payment."""
    url = reverse("payment_webhook")
    payload = {
        "EventTypeId": 1796,
        "EventData": {
            "TransactionId": "TX404",
            "OrderCode": "ORD_DOES_NOT_EXIST",
        },
    }

    with translation.override("en"):
        response = client.post(url, data=payload, content_type="application/json")

    assert response.status_code == 404
    assert response.json()["message"] == "Payment not found"


@pytest.mark.django_db
def test_webhook_malformed_json_body(client):
    """Should return 500 for malformed JSON."""
    url = reverse("payment_webhook")

    bad_payload = "not-json-at-all"

    with translation.override("en"):
        response = client.post(url, data=bad_payload, content_type="application/json")

    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert "Expecting value" in data["message"]


@pytest.mark.django_db
def test_webhook_missing_order_code(client):
    """Should return 404 if OrderCode is missing from payload."""
    url = reverse("payment_webhook")
    payload = {
        "EventTypeId": 1796,
        "EventData": {
            "TransactionId": "TX123"
            # 🟥 Missing "OrderCode"
        },
    }

    with translation.override("en"):
        response = client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

    assert response.status_code == 404
    assert response.json()["status"] == "error"
    assert "Payment not found" in response.json()["message"]
