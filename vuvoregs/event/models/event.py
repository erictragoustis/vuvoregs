"""Models for the event application.

Defines models for events and their related entities.
"""

from collections import defaultdict

from django.conf import settings
from django.db import models
from django.db.models import Count, F, Q
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from .athlete import Athlete


class EventManager(models.Manager):
    """Custom manager for the Event model."""

    def available(self):
        """Return events that are currently open for registration and not full."""
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


class Event(models.Model):
    """An event that participants can register for."""

    name = models.CharField(_("Name"), max_length=255)
    date = models.DateField(_("Date"))
    image = models.ImageField(
        _("Image"), upload_to="images/event_images/", blank=True, null=True
    )
    location = models.CharField(_("Location"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="events",
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        help_text="Email address for event-related inquiries.",
    )
    max_participants = models.PositiveIntegerField(
        _("Max Participants"), null=True, blank=True
    )
    registration_start_date = models.DateTimeField(
        _("Registration Start Date"), null=True, blank=True
    )
    registration_end_date = models.DateTimeField(
        _("Registration End Date"), null=True, blank=True
    )
    is_available = models.BooleanField(_("Is Available"), default=True)

    objects = EventManager()

    def __str__(self):
        """Return a string representation of the event."""
        return self.name

    @cached_property
    def paid_athletes(self):
        """Return all athletes who have fully paid their registration for this event."""
        return Athlete.objects.filter(
            registration__event=self,
            registration__payment_status="paid",
        )

    @property
    def paid_athlete_count(self):
        """Return the number of athletes with paid registrations."""
        return self.paid_athletes.count()

    @property
    def available_slots_remaining(self):
        """Return the number of registration slots still available.

        Returns None if unlimited.
        """
        if self.max_participants is None:
            return None
        return max(self.max_participants - self.paid_athlete_count, 0)

    def is_registration_open(self):
        """Return True if the event is open for registration."""
        now_ = now()
        if not self.is_available or self.date < now_.date():
            return False
        if self.registration_start_date and self.registration_start_date > now_:
            return False
        if self.registration_end_date and self.registration_end_date < now_:
            return False
        if (
            self.max_participants is not None
            and self.paid_athlete_count >= self.max_participants
        ):
            return False
        return True

    def get_paid_athletes_by_pickup_point(self):
        """Returns a dictionary of pickup_point → list of paid athletes."""
        result = defaultdict(list)
        for athlete in self.paid_athletes.select_related("pickup_point"):
            if athlete.pickup_point:
                result[athlete.pickup_point].append(athlete)
        return result


class PickUpPoint(models.Model):
    """A location where race packages can be picked up for an event."""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="pickup_points",
    )
    name = models.CharField(_("Name"), max_length=255)
    address = models.TextField(_("Address"))
    working_hours = models.CharField(
        _("Working Hours"), max_length=255, help_text="e.g. Mon–Fri 9am–5pm"
    )

    def __str__(self):
        """Return a string representation of the pickup point."""
        return f"{self.name} ({self.event.name})"
