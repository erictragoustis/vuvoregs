"""Models for the event application.

Defines models for Packages.
"""

from django.db import models

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
    races = models.ManyToManyField("event.Race", related_name="packages")
    team_discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:  # noqa: D106
        constraints = [
            models.UniqueConstraint(
                fields=["event", "name"], name="unique_package_per_event"
            )
        ]

    def __str__(self):
        """Return a string representation of the race package."""
        return f"{self.name} - ({self.event.name})"


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
