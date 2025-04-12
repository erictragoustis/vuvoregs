"""Models for the event application.

Defines models for  races
"""

from decimal import Decimal

from django.db import models
from django.db.models import Count, F, Q
from django.utils import timezone


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

    def get_current_pricing_label(self):
        now = timezone.now()
        for tbp in self.time_based_prices.all():
            if tbp.start_date <= now <= tbp.end_date:
                return tbp.label
        return None

    def has_team_discount(self):
        return self.team_discount_threshold and self.base_price_team > Decimal("0.00")

    def get_team_price(self):
        """Return team price per athlete, if team discount applies."""
        if self.has_team_discount():
            return self.base_price_team
        return None


class RaceType(models.Model):
    """Represent a type of race (e.g., Marathon, Sprint)."""

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        """Return a string representation of the race type."""
        return self.name


class TimeBasedPrice(models.Model):
    race = models.ForeignKey(
        "event.Race", on_delete=models.CASCADE, related_name="time_based_prices"
    )
    label = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Adjustment to apply during this time window. Can be negative (discount) or positive (surcharge).",
    )

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.label}: €{self.price_adjustment:+.2f} ({self.start_date.date()}–{self.end_date.date()})"
