"""Models for the event application.

Defines models for T&C's.
"""

from django.db import models


class TermsAndConditions(models.Model):
    """Represent terms and conditions for an event."""

    event = models.OneToOneField(
        "Event", on_delete=models.CASCADE, related_name="terms"
    )
    title = models.CharField(max_length=255, default="Terms and Conditions")
    content = models.TextField(help_text="You can use basic HTML or markdown.")
    version = models.CharField(max_length=20, default="1.0")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the terms and conditions."""
        return f"{self.title} (v{self.version}) for {self.event.name}"
