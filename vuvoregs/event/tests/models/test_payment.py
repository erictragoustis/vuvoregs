import json

import pytest
from django.urls import reverse

from event.models import Payment
from event.tests.factories import PaymentFactory


@pytest.mark.django_db
class TestPaymentModel:
    def test_get_registration_id_with_valid_json(self):
        """Should return registration ID when JSON is valid."""
        payment = PaymentFactory(extra_data=json.dumps({"registration_id": 42}))
        assert payment.get_registration_id() == 42

    def test_get_registration_id_with_invalid_json(self):
        """Should return None when extra_data is malformed."""
        payment = PaymentFactory(extra_data="{invalid json")
        assert payment.get_registration_id() is None

    def test_get_registration_id_with_missing_key(self):
        """Should return None when registration_id is missing."""
        payment = PaymentFactory(extra_data=json.dumps({"not_id": 1}))
        assert payment.get_registration_id() is None

    def test_get_success_url_with_id(self):
        """Should return success URL if registration_id exists."""
        payment = PaymentFactory(extra_data=json.dumps({"registration_id": 101}))
        expected_url = reverse("payment_success", args=[101])
        assert payment.get_success_url() == expected_url

    def test_get_success_url_fallback(self):
        """Should fallback to '/' if registration_id is missing."""
        payment = PaymentFactory(extra_data=json.dumps({}))
        assert payment.get_success_url() == "/"

    def test_get_failure_url_with_id(self):
        """Should return failure URL if registration_id exists."""
        payment = PaymentFactory(extra_data=json.dumps({"registration_id": 101}))
        expected_url = reverse("payment_failure", args=[101])
        assert payment.get_failure_url() == expected_url

    def test_get_failure_url_fallback(self):
        """Should fallback to '/' if registration_id is missing."""
        payment = PaymentFactory(extra_data="{}")
        assert payment.get_failure_url() == "/"
