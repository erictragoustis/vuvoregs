"""Models for the event application.

Defines models for Payment.
"""

import json

from django.db import models
from django.urls import reverse

from payments.models import BasePayment


class Payment(BasePayment):
    """Custom concrete Payment model with success/failure redirects."""

    order_code = models.CharField(max_length=50, blank=True, default="")

    def get_registration_id(self):
        """Extract the registration ID from the payment's extra data."""
        try:
            return json.loads(self.extra_data).get("registration_id")
        except Exception:
            return None

    def get_success_url(self):
        """Return the URL to redirect to upon successful payment."""
        reg_id = self.get_registration_id()
        return reverse("payment_success", args=[reg_id]) if reg_id else "/"

    def get_failure_url(self):
        """Return the URL to redirect to upon failed payment."""
        reg_id = self.get_registration_id()
        return reverse("payment_failure", args=[reg_id]) if reg_id else "/"
