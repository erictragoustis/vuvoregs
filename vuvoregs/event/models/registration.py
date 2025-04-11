"""Models for the event application.

Defines models for registration.
"""

from django.db import models


class Registration(models.Model):
    """Represent a participant's registration for an event."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    PAYMENT_CHOICES = [
        ("not_paid", "Not Paid"),
        ("paid", "Paid"),
        ("failed", "Payment Failed"),
    ]

    event = models.ForeignKey(
        "event.Event", on_delete=models.CASCADE, related_name="registrations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="not_paid"
    )
    agreed_to_terms = models.ForeignKey(
        "event.TermsAndConditions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Terms agreed to at confirmation",
    )
    agrees_to_terms = models.BooleanField(default=False)
    payment = models.OneToOneField(
        "event.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registration",
    )

    def __str__(self):
        """Return a string representation of the registration."""
        date_str = (
            self.created_at.strftime("%Y-%m-%d") if self.created_at else "unsaved"
        )
        return f"Registration {self.id or 'unsaved'} - {self.status} ({date_str})"
