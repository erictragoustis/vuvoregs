"""Models for the event application.

Defines models for event-specific Terms and Conditions.
"""

from django.db import models


class TermsAndConditions(models.Model):
    """Represents a versioned set of Terms and Conditions for a specific event."""

    event = models.OneToOneField(
        "Event",
        on_delete=models.CASCADE,
        related_name="terms",
        help_text="Event this T&C version applies to.",
    )

    title = models.CharField(
        max_length=255,
        default="Terms and Conditions",
        help_text="Title for internal/admin reference.",
    )

    content = models.TextField(
        help_text="You can use basic HTML or markdown for formatting."
    )

    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version string for tracking agreement history.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Return a string representation of the T&Cs for admin/display."""
        return f"{self.title} (v{self.version}) for {self.event.name}"
