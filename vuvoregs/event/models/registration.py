"""Models for the event application.

Defines models for registration records and payment tracking.
"""

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class Registration(models.Model):
    """Represents a participant's registration for an event.

    Includes payment tracking and status metadata.
    """

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    ]

    PAYMENT_CHOICES = [
        ("not_paid", _("Not Paid")),
        ("paid", _("Paid")),
        ("failed", _("Payment Failed")),
    ]

    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("Event"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text=_("Current processing status of the registration."),
        verbose_name=_("Status"),
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Total amount due for this registration."),
        verbose_name=_("Total Amount"),
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="not_paid",
        help_text=_("Payment status (paid, not paid, failed)."),
        verbose_name=_("Payment Status"),
    )

    agreed_to_terms = models.ForeignKey(
        "event.TermsAndConditions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Specific terms document agreed to by the user."),
        verbose_name=_("Agreed Terms Version"),
    )

    agrees_to_terms = models.BooleanField(
        default=False,
        help_text=_("Indicates whether user actively agreed to the terms."),
        verbose_name=_("Agrees to Terms"),
    )

    payment = models.OneToOneField(
        "event.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registration",
        help_text=_("Optional link to payment object (Viva, Stripe, etc)."),
        verbose_name=_("Payment"),
    )

    def __str__(self) -> str:
        """Return a string summary for debugging and admin display."""
        date_str = (
            self.created_at.strftime("%Y-%m-%d") if self.created_at else "unsaved"
        )
        return f"Registration {self.id or 'unsaved'} – {self.status} on {date_str}"

    def calculate_total_amount(self) -> Decimal:
        """Calculate total amount for this registration by summing all athlete-level totals."""  # noqa: E501
        return sum(athlete.get_total_price() for athlete in self.athletes.all())

    def update_total_amount(self) -> None:
        """Updates the stored total_amount based on current athlete values."""
        self.total_amount = self.calculate_total_amount()
        self.save(update_fields=["total_amount"])

    def is_paid(self) -> bool:
        """Return True if payment was successfully completed."""
        return self.payment_status == "paid"

    def mark_paid(self) -> None:
        """Set the registration as paid."""
        self.payment_status = "paid"
        self.status = "completed"
        self.save(update_fields=["payment_status", "status"])

    def mark_failed(self) -> None:
        """Set the registration status as failed."""
        self.payment_status = "failed"
        self.status = "failed"
        self.save(update_fields=["payment_status", "status"])
