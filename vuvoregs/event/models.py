from django.db import models
from django.core.exceptions import ValidationError
import json
from django.utils.timezone import now
from django.db.models import Q, Count, F
from django.utils.functional import cached_property

class EventManager(models.Manager):
    def available(self):
        return self.get_queryset().annotate(
            num_athletes=Count(
                'registrations__athletes',
                filter=Q(registrations__payment_status='paid'),
                distinct=True
            )
        ).filter(
            is_available=True,
            date__gte=now().date(),
            registration_start_date__lte=now(),
            registration_end_date__gte=now(),
        ).filter(
            Q(max_participants__isnull=True) |
            Q(num_athletes__lt=F('max_participants'))
        )

class RaceManager(models.Manager):
    def available(self):
        return self.get_queryset().annotate(
            num_athletes=Count(
                'athlete',
                filter=Q(athlete__registration__payment_status='paid'),
                distinct=True
            )
        ).filter(
            Q(max_participants__isnull=True) |
            Q(num_athletes__lt=F('max_participants'))
        )

class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_start_date = models.DateTimeField(null=True, blank=True)
    registration_end_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    objects = EventManager()

    @cached_property
    def paid_athletes(self):
        from .models import Athlete  # Avoid circular imports
        return Athlete.objects.filter(
            registration__event=self,
            registration__payment_status='paid'
        )

    @property
    def paid_athlete_count(self):
        return self.paid_athletes.count()

    def is_registration_open(self):
        if not self.is_available or self.date < now().date():
            return False
        if self.registration_start_date and self.registration_start_date > now():
            return False
        if self.registration_end_date and self.registration_end_date < now():
            return False

        current_athletes = self.registrations.aggregate(
            count=Count('athletes', distinct=True)
        )['count'] or 0

        return (
            self.max_participants is None 
            or current_athletes < self.max_participants
        )

    def __str__(self):
        return self.name

class PickUpPoint(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='pickup_points'
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    working_hours = models.CharField(max_length=255, help_text="e.g. Mon–Fri 9am–5pm")

    def __str__(self):
        return f"{self.name} ({self.event.name})"

class RaceType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Race(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    event = models.ForeignKey(Event, related_name='races', on_delete=models.CASCADE)
    race_type = models.ForeignKey(RaceType, related_name='races', on_delete=models.CASCADE)
    race_km = models.DecimalField(max_digits=5, decimal_places=2)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    min_participants = models.PositiveIntegerField(null=True, blank=True)

    objects = RaceManager()

    def is_open(self):
        if not self.event.is_registration_open():
            return False
        current_athletes = self.athlete_set.count()
        return (
            self.max_participants is None 
            or current_athletes < self.max_participants
        )

    def __str__(self):
        return f"{self.name} - {self.race_type.name} - {self.race_km} KM ({self.event.name})"

class RacePackage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    races = models.ManyToManyField(Race, related_name="packages")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'name'], name='unique_package_per_event')
        ]

    def __str__(self):
        return f"{self.name} - ({self.event.name})"

class PackageOption(models.Model):
    package = models.ForeignKey(RacePackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    options_json = models.JSONField(default=list, blank=True)
    options_string = models.CharField(max_length=500, blank=True, null=True)

    def set_options_from_string(self, options_string):
        if options_string:
            options_list = [opt.strip() for opt in options_string.split(',') if opt.strip()]
            self.options_json = options_list
        else:
            self.options_json = []
        self.options_string = options_string
        self.save()

    def __str__(self):
        return self.name

class Registration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    PAYMENT_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='not_paid')

    def __str__(self):
        return f"Registration {self.id} - {self.status} ({self.created_at.strftime('%Y-%m-%d')})"

class Athlete(models.Model):
    registration = models.ForeignKey(
        Registration, 
        on_delete=models.CASCADE, 
        related_name="athletes"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    sex = models.CharField(
        max_length=10, 
        choices=[('Male', 'Male'), ('Female', 'Female')]
    )
    dob = models.DateField(blank=True, null=True)
    hometown = models.CharField(max_length=100)
    race = models.ForeignKey("Race", on_delete=models.CASCADE)
    package = models.ForeignKey("RacePackage", on_delete=models.CASCADE)
    bib_number = models.CharField(max_length=10, blank=True, null=True)
    pickup_point = models.ForeignKey(
        PickUpPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='athletes'
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    selected_options = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.race.race_type.name}"

    def save(self, *args, **kwargs):
        """
        Ensure 'selected_options' is at least an empty dict so it's JSON-serializable.
        """
        if not isinstance(self.selected_options, dict):
            # If it's None or any other type, default to empty dict
            self.selected_options = {}

        # Make sure the data is JSON-serializable (avoid weird nested structures)
        self.selected_options = json.loads(json.dumps(self.selected_options))
        super().save(*args, **kwargs)

    def clean(self):
        """
        Enforce that if a package has PackageOption objects,
        the user must fill out each one in 'selected_options'.
        """
        super().clean()

        # 🛡️ Defensive check for missing FK
        package = getattr(self, 'package', None)
        if package and package.packageoption_set.exists():
            if not isinstance(self.selected_options, dict):
                raise ValidationError("Package options must be filled out.")

            expected_option_names = [
                opt.name
                for opt in package.packageoption_set.all()
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

