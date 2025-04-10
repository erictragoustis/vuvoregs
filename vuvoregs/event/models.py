"""Models for the event application.

Defines models for events, races, registrations, athletes, and related entities.
Includes custom managers and utility methods for querying and managing data.
"""

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.timezone import now
from payments.models import BasePayment


class EventManager(models.Manager):
    """Custom manager for the Event model."""

    def available(self):
        """Return events that are available for registration."""
        return (
            self.get_queryset()
            .annotate(
                num_athletes=Count(
                    "registrations__athletes",
                    filter=Q(registrations__payment_status="paid"),
                    distinct=True,
                )
            )
            .filter(
                is_available=True,
                date__gte=now().date(),
                registration_start_date__lte=now(),
                registration_end_date__gte=now(),
            )
            .filter(
                Q(max_participants__isnull=True)
                | Q(num_athletes__lt=F("max_participants"))
            )
        )


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


class Event(models.Model):
    """Represent an event that users can register for."""

    name = models.CharField(max_length=255)
    date = models.DateField()
    image = models.ImageField(upload_to="images/event_images/", blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="events",
    )
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_start_date = models.DateTimeField(null=True, blank=True)
    registration_end_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    objects = EventManager()

    def __str__(self):
        """Return a string representation of the event."""
        return self.name

    @cached_property
    def paid_athletes(self):
        """Return a queryset of athletes who have paid for this event."""
        from .models import Athlete  # Avoid circular imports

        return Athlete.objects.filter(
            registration__event=self,
            registration__payment_status="paid",
        )

    @property
    def paid_athlete_count(self):
        """Return the count of paid athletes for this event."""
        return self.paid_athletes.count()

    def is_registration_open(self):
        """Check if the registration for this event is currently open."""
        if not self.is_available or self.date < now().date():
            return False
        if self.registration_start_date and self.registration_start_date > now():
            return False
        if self.registration_end_date and self.registration_end_date < now():
            return False

        current_athletes = (
            self.registrations.aggregate(count=Count("athletes", distinct=True))[
                "count"
            ]
            or 0
        )

        return self.max_participants is None or current_athletes < self.max_participants


class PickUpPoint(models.Model):
    """Represent a pickup point for an event."""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="pickup_points",
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    working_hours = models.CharField(max_length=255, help_text="e.g. Mon–Fri 9am–5pm")

    def __str__(self):
        """Return a string representation of the pickup point."""
        return f"{self.name} ({self.event.name})"


class RaceType(models.Model):
    """Represent a type of race (e.g., Marathon, Sprint)."""

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        """Return a string representation of the race type."""
        return self.name


class Race(models.Model):
    """Represent a race within an event."""

    name = models.CharField(max_length=255, blank=True)
    event = models.ForeignKey(Event, related_name="races", on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to="images/event_images/race_images", blank=True, null=True
    )
    race_type = models.ForeignKey(
        RaceType, related_name="races", on_delete=models.CASCADE
    )
    race_km = models.DecimalField(max_digits=5, decimal_places=2)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    min_participants = models.PositiveIntegerField(null=True, blank=True)

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


class RacePackage(models.Model):
    """Represent a package of races offered for an event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    races = models.ManyToManyField(Race, related_name="packages")
    team_discount_threshold = models.PositiveIntegerField(
        null=True, blank=True
    )  # e.g. 5 athletes
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


class Registration(models.Model):
    """Represent a participant's registration for an event."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    PAYMENT_CHOICES = [
        ("not_paid", "Not Paid"),
        ("paid", "Paid"),
        ("failed", "Payment Failed"),
    ]

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="not_paid"
    )
    payment = models.OneToOneField(
        "event.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registration",
    )

    def __str__(self):
        """Return a string representation of the registration."""
        return f"Registration {self.id} - {self.status} ({self.created_at.strftime('%Y-%m-%d')})"  # noqa: E501


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


class PackageSpecialPrice(models.Model):
    """Represent special pricing for a race package."""

    package = models.ForeignKey(
        "RacePackage", on_delete=models.CASCADE, related_name="special_prices"
    )
    event = models.ForeignKey("Event", on_delete=models.CASCADE, null=True, blank=True)
    race = models.ForeignKey("Race", on_delete=models.CASCADE, null=True, blank=True)
    label = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        """Return a string representation of the special price."""
        return f"{self.label} - €{self.price} ({self.package.name})"


class Athlete(models.Model):
    """Represent an athlete participating in a race."""

    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="athletes",
    )
    special_price_option = models.ForeignKey(
        PackageSpecialPrice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Chosen special price for this athlete",
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
        PickUpPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athletes",
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    selected_options = models.JSONField(null=True, blank=True)
    agreed_to_terms = models.ForeignKey(
        TermsAndConditions,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agreements",
    )
    agrees_to_terms = models.BooleanField(default=False)

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

    def get_final_price(self):
        """Get final Price."""
        package = self.package
        registration = self.registration

        # Apply special price if selected
        if self.special_price_option and self.special_price_option.package == package:
            return self.special_price_option.price

        # Apply team discount
        if package.team_discount_threshold and package.team_discount_price:
            team_size = registration.athletes.count()
            if team_size >= package.team_discount_threshold:
                return package.team_discount_price

        return package.price

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


class Payment(BasePayment):
    """Custom concrete Payment model with success/failure redirects."""

    def get_registration_id(self):
        """Extract the registration ID from the payment's extra data."""
        try:
            return json.loads(self.extra_data).get("registration_id")
        except Exception:
            return None

    def get_success_url(self):
        """Return the URL to redirect to upon successful payment."""
        reg_id = self.get_registration_id()
        return reverse("payment_success", args=[reg_id]) if reg_id else "/"

    def get_failure_url(self):
        """Return the URL to redirect to upon failed payment."""
        reg_id = self.get_registration_id()
        return reverse("payment_failure", args=[reg_id]) if reg_id else "/"
