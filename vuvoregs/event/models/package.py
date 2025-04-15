"""Models for the event application.

Defines models for Packages.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# from event.models import Event, Race


class RacePackage(models.Model):
    """Represent a package of races offered for an event."""

    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="packages",
        verbose_name=_("Event"),
    )
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"))
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_("Adjustment applied to race base price"),
        verbose_name=_("Price Adjustment"),
    )
    visible_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "Package will be hidden after this datetime. Leave blank to always show."
        ),
        verbose_name=_("Visible Until"),
    )
    races = models.ManyToManyField(
        "event.Race",
        related_name="packages",
        verbose_name=_("Races"),
    )

    class Meta:
        """Meta information for the RacePackage model."""

        constraints = [
            models.UniqueConstraint(
                fields=["event", "name"], name="unique_package_per_event"
            )
        ]

    def __str__(self):
        """Return a string representation of the race package."""
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

    def get_final_price(self, is_team: bool = False) -> Decimal:
        """Return the final price of this package including.

        - base race price (individual or team)
        - package adjustment
        - time-based adjustment
        """
        race = self.get_race()
        if not race:
            return Decimal("0.00")

        if is_team and race.has_team_discount():
            base = race.base_price_team
        else:
            base = race.base_price_individual

        return (
            base
            + (self.price_adjustment or Decimal("0.00"))
            + self.get_active_time_adjustment()
        )

    def set_display_price(self, race):
        """Attach final and team price display attributes based on the given race."""
        self.final_price_display = self.get_final_price(is_team=False)
        self.team_price_display = (
            self.get_final_price(is_team=True) if race.has_team_discount() else None
        )

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
        """Check if this package has a team discount available."""
        return self.team_discount_threshold and self.team_discount_price

    @property
    def race(self):
        """Return the first race associated with this package."""
        return self.races.first()

    @property
    def final_price(self) -> Decimal:
        """Shortcut for template use: returns individual final price."""
        return self.get_final_price(is_team=False)

    @property
    def team_final_price(self) -> Decimal:
        """Returns the final team price for use in templates."""
        return self.get_final_price(is_team=True)


class PackageOption(models.Model):
    """Represent additional options for a race package."""

    package = models.ForeignKey(
        RacePackage,
        on_delete=models.CASCADE,
        verbose_name=_("Package"),
    )
    name = models.CharField(_("Option Name"), max_length=255)
    options_json = models.JSONField(
        default=list, blank=True, verbose_name=_("Options (JSON)")
    )
    options_string = models.CharField(
        max_length=500, blank=True, verbose_name=_("Options String")
    )

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
        "Race",
        on_delete=models.CASCADE,
        related_name="special_prices",
        verbose_name=_("Race"),
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the special price, e.g., 'Domestic Citizen'"),
        verbose_name=_("Internal Name"),
    )
    label = models.CharField(_("Display Label"), max_length=255)
    description = models.TextField(
        blank=True,
        help_text=_("Description of the special price, if applicable."),
        verbose_name=_("Description"),
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Discount subtracted from base race price"),
        verbose_name=_("Discount Amount"),
    )
    document = models.FileField(
        upload_to="special_price_docs/",
        blank=True,
        null=True,
        help_text=_("Optional declaration form athletes must show."),
    )

    def __str__(self):
        """Return a string representation of the race special price."""
        return f"{self.label} – −€{self.discount_amount:.2f} for {self.race.name}"
