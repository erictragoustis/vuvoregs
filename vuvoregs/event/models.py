# models.py
from django.db import models
from django.core.exceptions import ValidationError
import json
from django.utils.timezone import now
from django.db.models import Q, Count, F

class EventManager(models.Manager):
    def available(self):
        return self.get_queryset().annotate(
            num_athletes=Count('registrations__athletes', distinct=True)
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
            num_athletes=Count('registration__athletes', distinct=True)
        ).filter(
            Q(max_participants__isnull=True) |
            Q(num_athletes__lt=F('max_participants'))
        )

class Event(models.Model):
    """Represents a race event."""
    name = models.CharField(max_length=255)
    date = models.DateField()
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of participants allowed for the event.")
    registration_start_date = models.DateTimeField(null=True, blank=True,)
    registration_end_date = models.DateTimeField(null=True, blank=True,)
    is_available = models.BooleanField(default=True)
    objects = EventManager()

    def __str__(self):
        return self.name


class RaceType(models.Model):
    """Defines the type of race (e.g., Marathon, Trail, Relay)."""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    objects = RaceManager()

    def __str__(self):
        return self.name


class Race(models.Model):
    """Each event has specific races, associated with a race type."""
    name = models.CharField(max_length=255, null=True, blank=True)
    event = models.ForeignKey(Event, related_name='races', on_delete=models.CASCADE)
    race_type = models.ForeignKey(RaceType, related_name='races', on_delete=models.CASCADE)
    race_km = models.DecimalField(max_digits=5, decimal_places=2)
    max_participants = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of participants required for the race.")
    min_participants = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum number of participants required for the race.")

    def __str__(self):
        return f"{self.name} - {self.race_type.name} - {self.race_km} KM ({self.event.name})"


class RacePackage(models.Model):
    """Each race has specific packages (e.g., Basic, Premium)."""
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
    options_string = models.CharField(max_length=500, blank=True, null=True, editable=False)

    def set_options_from_string(self, options_string):
        """Converts a comma-separated string to a JSON list."""
        if options_string:
            options_list = [opt.strip() for opt in options_string.split(',')]
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
    """Represents an athlete registering for a race."""
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="athletes")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    sex = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    dob = models.DateField(blank=True, null=True)
    hometown = models.CharField(max_length=100)
    race = models.ForeignKey("Race", on_delete=models.CASCADE)
    package = models.ForeignKey("RacePackage", on_delete=models.CASCADE)
    bib_number = models.CharField(max_length=10, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    selected_options = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.race.race_type.name}"
    
    def save(self, *args, **kwargs):
        if isinstance(self.selected_options, dict):
            self.selected_options = json.loads(json.dumps(self.selected_options))  # Ensure JSON format
        print("Saving selected_options:", json.dumps(self.selected_options, indent=2))
        super().save(*args, **kwargs)

    def clean(self):
        """Ensure JSON format for selected options."""
        if self.selected_options is not None and not isinstance(self.selected_options, dict):
            raise ValidationError("Selected options must be a valid JSON dictionary.")
