"""Models for the event application.

Defines models for events, races, registrations, athletes, and related entities.
Includes custom managers and utility methods for querying and managing data.
"""

from decimal import Decimal
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Athlete(models.Model):
    """Represents a single athlete participating in a race.

    Each athlete is linked to a registration, race, and package.
    Package extras and race pricing rules determine final cost.
    """

    registration = models.ForeignKey(
        "event.Registration",
        on_delete=models.CASCADE,
        related_name="athletes",
    )

    special_price = models.ForeignKey(
        "event.RaceSpecialPrice",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Race-level special price (discount).",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    fathers_name = models.CharField(max_length=100, blank=True)
    team = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    sex = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female")],
    )

    dob = models.DateField(blank=True, null=True)
    hometown = models.CharField(max_length=100)

    race = models.ForeignKey("Race", on_delete=models.CASCADE)
    package = models.ForeignKey("RacePackage", on_delete=models.CASCADE)

    bib_number = models.CharField(max_length=10, blank=True)

    pickup_point = models.ForeignKey(
        "event.PickUpPoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athletes",
    )

    registration_date = models.DateTimeField(auto_now_add=True)

    selected_options = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Package customization options selected by athlete (T-shirt size, etc)."
        ),
    )

    class Meta:
        """Metadata options for the Athlete model."""

        ordering = ["-registration__created_at"]

    def __str__(self) -> str:
        """Return a string representation of the athlete."""
        return f"{self.first_name} {self.last_name} – {self.race.race_type.name}"

    def save(self, *args, **kwargs) -> None:
        """Ensure selected options are a valid JSON dict before saving."""
        if not isinstance(self.selected_options, dict):
            self.selected_options = {}
        self.selected_options = json.loads(json.dumps(self.selected_options))
        super().save(*args, **kwargs)

    def get_time_based_adjustment(self) -> Decimal:
        """Return the current time-based price adjustment for the athlete's race."""
        now = timezone.now()
        tbp = self.race.time_based_prices.filter(
            start_date__lte=now, end_date__gte=now
        ).first()
        return tbp.price_adjustment if tbp else Decimal("0.00")

    def get_total_price(self) -> Decimal:
        """Calculate the final price for this athlete.

        Formula:
            base (team or individual)
          + time-based adjustment
          + package adjustment
          - race-level special discount
        """
        race = self.race
        registration = self.registration
        team_size = registration.athletes.count()

        is_team = (
            race.team_discount_threshold and team_size >= race.team_discount_threshold
        )

        base_price = race.base_price_team if is_team else race.base_price_individual
        discount = (
            self.special_price.discount_amount
            if self.special_price
            else Decimal("0.00")
        )
        package_adj = self.package.price_adjustment or Decimal("0.00")
        time_adj = self.get_time_based_adjustment()

        return base_price + package_adj + time_adj - discount

    def clean(self) -> None:
        """Validate that all required package options have been selected."""
        super().clean()
        if not isinstance(self.selected_options, dict):
            raise ValidationError("Package options must be filled out.")

        expected = [opt.name for opt in self.package.packageoption_set.all()]
        missing = [
            name
            for name in expected
            if name not in self.selected_options or not self.selected_options[name]
        ]
        if missing:
            raise ValidationError(
                f"You must select a valid choice for: {', '.join(missing)}"
            )
