"""Models for the event application.

Defines models for Packages.
"""

from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone

# from event.models import Event, Race


class RacePackage(models.Model):
    """Represent a package of races offered for an event."""

    event = models.ForeignKey(
        "event.Event", on_delete=models.CASCADE, related_name="packages"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Adjustment applied to race base price",
    )
    visible_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Package will be hidden after this datetime. Leave blank to always show.",
    )
    races = models.ManyToManyField("event.Race", related_name="packages")
    team_discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "name"], name="unique_package_per_event"
            )
        ]

    def __str__(self):
        return f"{self.name} - ({self.event.name})"

    def is_visible_now(self):
        """Check if this package is currently visible."""
        return not self.visible_until or self.visible_until > timezone.now()

    def get_race(self):
        """Return the first race associated (assumes one-to-one usage)."""
        return self.races.first()

    def get_active_time_adjustment(self):
        """Returns the currently active time-based price adjustment, if any."""
        race = self.get_race()
        if not race:
            return Decimal("0.00")
        now = timezone.now()
        for tbp in race.time_based_prices.all():
            if tbp.start_date <= now <= tbp.end_date:
                return tbp.price_adjustment
        return Decimal("0.00")

    def get_current_final_price(self):
        """Return final price including race base, package adjustment, and time-based adjustment."""
        race = self.get_race()
        if not race:
            return None
        base = race.base_price_individual or Decimal("0.00")
        adjustment = self.price_adjustment or Decimal("0.00")
        return base + adjustment + self.get_active_time_adjustment()

    def get_savings_amount(self):
        """Return savings compared to race base price, if any."""
        race = self.get_race()
        if not race:
            return Decimal("0.00")
        return race.base_price_individual - self.get_current_final_price()

    def has_discount(self):
        """Check if this package is discounted compared to base race price."""
        race = self.get_race()
        if not race:
            return False
        return self.get_current_final_price() < race.base_price_individual

    def has_team_discount(self):
        return self.team_discount_threshold and self.team_discount_price

    @property
    def race(self):
        return self.races.first()


class PackageOption(models.Model):
    """Represent additional options for a race package."""

    package = models.ForeignKey(RacePackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    options_json = models.JSONField(default=list, blank=True)
    options_string = models.CharField(max_length=500, blank=True)

    def __str__(self):
        """Return a string representation of the package option."""
        return self.name

    def set_options_from_string(self, options_string):
        """Convert a comma-separated string of options into a JSON list."""
        if options_string:
            options_list = [
                opt.strip() for opt in options_string.split(",") if opt.strip()
            ]  # noqa: E501
            self.options_json = options_list
        else:
            self.options_json = []
        self.options_string = options_string
        self.save()


class RaceSpecialPrice(models.Model):
    """Represent special pricing for a race."""

    race = models.ForeignKey(
        "Race", on_delete=models.CASCADE, related_name="special_prices"
    )
    label = models.CharField(max_length=255)

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Discount subtracted from base race price",
    )

    def __str__(self):
        """Return a string representation of the race special price."""
        return f"{self.label} – −€{self.discount_amount:.2f} for {self.race.name}"
