"""Models for the event application.

Defines models for events, races, registrations, athletes, and related entities.
Includes custom managers and utility methods for querying and managing data.
"""

import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Athlete(models.Model):
    """Represent an athlete participating in a race."""

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
        help_text="Race-level special price (discount)",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
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
    selected_options = models.JSONField(null=True, blank=True)

    class Meta:
        """Meta options for the Athlete model.

        Defines ordering and other metadata for the Athlete model.
        """

        ordering = ["-registration__created_at"]

    def __str__(self):
        """Return a string representation of the athlete."""
        return f"{self.first_name} {self.last_name} - {self.race.race_type.name}"

    def save(self, *args, **kwargs):
        """Ensure 'selected_options' is JSON-serializable."""
        if not isinstance(self.selected_options, dict):
            self.selected_options = {}
        self.selected_options = json.loads(json.dumps(self.selected_options))
        super().save(*args, **kwargs)

    def get_time_based_adjustment(self) -> float:
        """Return the price adjustment for the current time window, if any."""
        now = timezone.now()
        for tbp in self.race.time_based_prices.all():
            if tbp.start_date <= now <= tbp.end_date:
                return tbp.price_adjustment
        return 0

    def get_final_price(self):
        """Calculate the athlete's final price.

        base price (individual or team) - race-level special discount + package adjustment
        """  # noqa: E501
        race = self.race
        registration = self.registration
        team_size = registration.athletes.count()

        is_team = (
            race.team_discount_threshold and team_size >= race.team_discount_threshold
        )

        base_price = race.base_price_team if is_team else race.base_price_individual

        # Apply race-level special price (discount)
        discount = self.special_price.discount_amount if self.special_price else 0
        package_adjustment = self.package.price_adjustment
        time_adjustment = self.get_time_based_adjustment()

        return base_price + package_adjustment + time_adjustment - discount

    def clean(self):
        """Validate that all required package options are selected."""
        super().clean()
        package = getattr(self, "package", None)
        if package and package.packageoption_set.exists():
            if not isinstance(self.selected_options, dict):
                raise ValidationError("Package options must be filled out.")
            expected_option_names = [
                opt.name for opt in package.packageoption_set.all()
            ]
            missing = [
                name
                for name in expected_option_names
                if name not in self.selected_options or not self.selected_options[name]
            ]
            if missing:
                raise ValidationError(
                    f"You must select a valid choice for: {', '.join(missing)}"
                )
