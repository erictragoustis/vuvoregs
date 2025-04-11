"""Models for the event application.

Defines models for  races
"""

from django.db import models
from django.db.models import Count, F, Q


class RaceManager(models.Manager):
    """Custom manager for the Race model."""

    def available(self):
        """Return races that are available for registration."""
        return (
            self.get_queryset()
            .annotate(
                num_athletes=Count(
                    "athlete",
                    filter=Q(athlete__registration__payment_status="paid"),
                    distinct=True,
                )
            )
            .filter(
                Q(max_participants__isnull=True)
                | Q(num_athletes__lt=F("max_participants"))
            )
        )


class Race(models.Model):
    """Represent a race within an event."""

    name = models.CharField(max_length=255, blank=True)
    event = models.ForeignKey(
        "event.Event", related_name="races", on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to="images/event_images/race_images", blank=True, null=True
    )
    race_type = models.ForeignKey(
        "event.RaceType", related_name="races", on_delete=models.CASCADE
    )
    race_km = models.DecimalField(max_digits=5, decimal_places=2)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    min_participants = models.PositiveIntegerField(null=True, blank=True)
    base_price_individual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Base price for individual registrations",
    )
    base_price_team = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Base price per athlete for team registrations",
    )
    team_discount_threshold = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum number of athletes for team pricing to apply",
    )

    objects = RaceManager()

    def __str__(self):
        """Return a string representation of the race."""
        return f"{self.name} - {self.race_type.name} - {self.race_km} KM ({self.event.name})"  # noqa: E501

    def is_open(self):
        """Check if the race is open for registration."""
        if not self.event.is_registration_open():
            return False
        current_athletes = self.athlete_set.count()
        return self.max_participants is None or current_athletes < self.max_participants


class RaceType(models.Model):
    """Represent a type of race (e.g., Marathon, Sprint)."""

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        """Return a string representation of the race type."""
        return self.name
