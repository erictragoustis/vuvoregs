"""Models for the event application.

Defines models for events, races, registrations, athletes, and related entities.
Includes custom managers and utility methods for querying and managing data.
"""

from decimal import Decimal
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Athlete(models.Model):
    """Represents a single athlete participating in a race.

    Each athlete is linked to a registration, race, and package.
    Package extras and race pricing rules determine final cost.
    """

    registration = models.ForeignKey(
        "event.Registration",
        on_delete=models.CASCADE,
        related_name="athletes",
        verbose_name=_("Registration"),
    )

    special_price = models.ForeignKey(
        "event.RaceSpecialPrice",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Special Price"),
        help_text=_("Race-level special price (discount)."),
    )

    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    fathers_name = models.CharField(_("Father's Name"), max_length=100, blank=True)
    team = models.CharField(_("Team"), max_length=100, blank=True)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone"), max_length=20)

    sex = models.CharField(
        _("Sex"),
        max_length=10,
        choices=[("Male", _("Male")), ("Female", _("Female"))],
    )

    dob = models.DateField(_("Date of Birth"), blank=True, null=True)
    hometown = models.CharField(_("Hometown"), max_length=100)

    race = models.ForeignKey("Race", on_delete=models.CASCADE, verbose_name=_("Race"))
    package = models.ForeignKey(
        "RacePackage", on_delete=models.CASCADE, verbose_name=_("Package")
    )

    bib_number = models.CharField(_("Bib Number"), max_length=10, blank=True)

    pickup_point = models.ForeignKey(
        "event.PickUpPoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athletes",
        verbose_name=_("Pickup Point"),
    )

    role = models.ForeignKey(
        "event.RaceRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("The athlete's assigned role (e.g., Runner, Cyclist)"),
    )

    registration_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Registration Date")
    )

    selected_options = models.JSONField(
        null=True,
        blank=True,
        help_text=_(
            "Package customization options selected by athlete (T-shirt size, etc)."
        ),
        verbose_name=_("Selected Options"),
    )

    class Meta:
        """Metadata options for the Athlete model."""

        ordering = ["-registration__created_at"]
        verbose_name = _("Athlete")
        verbose_name_plural = _("Athletes")

    def __str__(self) -> str:
        """Return a string representation of the athlete."""
        try:
            return f"{self.first_name} {self.last_name} – {self.race.race_type.name}"
        except Exception:
            return f"{self.first_name} {self.last_name}"

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

    def is_minor(self) -> bool:
        """Return True if athlete is under 18 on the event date."""
        if not self.dob or not self.race or not self.race.event:
            return False
        age_at_event = (
            self.race.event.date - self.dob
        ).days // 365.25  # approximate in years
        return age_at_event < 18

    def get_total_price(self) -> Decimal:
        """Calculate and return the total price for the athlete's registration.

        The total price is determined by combining the base price, package adjustment,
        time-based adjustment, and subtracting any applicable discounts.
        """
        is_team = self.registration.qualifies_for_team_discount(self.race)

        base_price = (
            self.race.base_price_team if is_team else self.race.base_price_individual
        )
        discount = (
            self.special_price.discount_amount
            if self.special_price
            else Decimal("0.00")
        )
        package_adj = self.package.price_adjustment or Decimal("0.00")
        time_adj = self.get_time_based_adjustment()

        return base_price + package_adj + time_adj - discount

    def clean(self):
        """Validate that selected_options is a proper dict and required options are filled."""
        super().clean()

        # 🧼 Ensure selected_options is at least a dict
        if self.selected_options is None:
            self.selected_options = {}

        if not isinstance(self.selected_options, dict):
            raise ValidationError(_("Package options must be a dictionary."))

        try:
            package = self.package
        except models.ObjectDoesNotExist:
            return  # No valid package yet — skip validation

        # 🔍 Check for missing required options
        required_options = [opt.name for opt in self.package.packageoption_set.all()]
        missing = [
            name
            for name in required_options
            if name not in self.selected_options
            or not any(v.strip() for v in self.selected_options[name])
        ]

        if missing:
            raise ValidationError(
                _("Missing selections for: %(missing)s.")
                % {"missing": ", ".join(missing)}
            )

        # 🔒 Validate selected values are among allowed options (if options_json is defined)
        for option in self.package.packageoption_set.all():
            selected = self.selected_options.get(option.name, [])
            if not isinstance(selected, list):
                selected = [selected]
            allowed = option.options_json
            for value in selected:
                if value not in allowed:
                    raise ValidationError(
                        _(f"Invalid value '{value}' for option '{option.name}'.")
                    )

        # ✅ Validate role if the race requires roles
        if self.race and self.race.requires_roles():
            allowed = self.race.get_allowed_roles()
            if self.role not in allowed:
                raise ValidationError({
                    "role": _("Invalid role. Must be one of: %(roles)s.")
                    % {"roles": ", ".join(str(r) for r in allowed)}
                })
        print("💾 selected_options =", self.selected_options)
