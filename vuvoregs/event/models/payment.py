"""Models for the event application.

Defines models for Payment processing and redirects.
"""

import json

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from payments.models import BasePayment


class Payment(BasePayment):
    """Custom Payment model for storing extra metadata.

    generating success/failure redirection URLs.
    """

    order_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Optional external order reference or code."),
        verbose_name=_("Order Code"),
    )

    def get_registration_id(self) -> int | None:
        """Extract the registration ID from extra_data JSON."""
        try:
            return json.loads(self.extra_data).get("registration_id")
        except (TypeError, ValueError, AttributeError):
            return None

    def get_success_url(self) -> str:
        """Return the redirect URL for successful payment.

        Falls back to home if ID missing.
        """
        reg_id = self.get_registration_id()
        return reverse("payment_success", args=[reg_id]) if reg_id else "/"

    def get_failure_url(self) -> str:
        """Return the redirect URL for failed payment.

        Falls back to home if ID missing.
        """
        reg_id = self.get_registration_id()
        return reverse("payment_failure", args=[reg_id]) if reg_id else "/"
