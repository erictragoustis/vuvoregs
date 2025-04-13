"""This module defines models related to races, including Race, RaceType, and TimeBasedPrice.

It also includes a custom manager for Race to handle specific queries and methods
to calculate pricing, discounts, and availability.
"""

from decimal import Decimal

from django.db import models
from django.db.models import Count, F, Q
from django.utils import timezone


class RaceManager(models.Manager):
    """Custom manager for the Race model."""

    def available(self):
        """Return races that are open for registration and not full."""
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
    """A race belonging to an event (e.g. 5K, 10K, Relay)."""

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
        default=Decimal("0.00"),
        help_text="Base price for individual registrations.",
    )
    base_price_team = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Base price per athlete for team registrations.",
    )
    team_discount_threshold = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum number of athletes for team pricing to apply.",
    )

    objects = RaceManager()

    def __str__(self):
        return f"{self.name} - {self.race_type.name} - {self.race_km} KM ({self.event.name})"

    def is_open(self):
        """Return True if the race can currently accept registrations."""
        if not self.event.is_registration_open():
            return False

        current_paid = self.athlete_set.filter(
            registration__payment_status="paid"
        ).count()

        return self.max_participants is None or current_paid < self.max_participants

    def has_team_discount(self) -> bool:
        """Return True if team pricing is enabled."""
        return bool(
            self.team_discount_threshold and self.base_price_team > Decimal("0.00")
        )

    def get_team_price(self) -> Decimal | None:
        """Return the team price per athlete (if eligible)."""
        return self.base_price_team if self.has_team_discount() else None

    def get_current_price_adjustment(self) -> Decimal:
        """Return any time-based price adjustment active right now."""
        now = timezone.now()
        current_window = self.time_based_prices.filter(
            start_date__lte=now, end_date__gte=now
        ).first()
        return current_window.price_adjustment if current_window else Decimal("0.00")

    def get_pricing_label(self) -> str | None:
        """Return the label of the active time-based pricing window."""
        now = timezone.now()
        tbp = self.time_based_prices.filter(
            start_date__lte=now, end_date__gte=now
        ).first()
        return tbp.label if tbp else None

    def get_effective_base_price(self, is_team: bool = False) -> Decimal:
        """Return the base price depending on whether it's an individual or team.

        Does not include package or option adjustments — just base race price.
        """
        base = (
            self.base_price_team
            if is_team and self.has_team_discount()
            else self.base_price_individual
        )
        return base + self.get_current_price_adjustment()


class RaceType(models.Model):
    """Type/category of a race (e.g. Marathon, Relay, Sprint)."""

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TimeBasedPrice(models.Model):
    """A time window with a pricing adjustment for a race."""

    race = models.ForeignKey(
        "event.Race", on_delete=models.CASCADE, related_name="time_based_prices"
    )
    label = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Adjustment to apply during this time window. Can be negative (discount) or positive (surcharge).",  # noqa: E501
    )

    class Meta:
        """Metadata options for the TimeBasedPrice model."""

        ordering = ["start_date"]

    def __str__(self):
        """Return a string representation of the time-based price."""
        return f"{self.label}: €{self.price_adjustment:+.2f} ({self.start_date.date()}–{self.end_date.date()})"
