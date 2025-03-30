from django.db import models

class Event(models.Model):
    """Represents a race event."""
    name = models.CharField(max_length=255)
    date = models.DateField()
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RaceType(models.Model):
    """Defines the type of race (e.g., Marathon, Trail, Relay)."""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Race(models.Model):
    """Each event has specific races, associated with a race type."""
    name = models.CharField(max_length=255, null=True, blank=True,)
    event = models.ForeignKey(Event, related_name='races', on_delete=models.CASCADE)
    race_type = models.ForeignKey(RaceType, related_name='races', on_delete=models.CASCADE)
    race_km = models.DecimalField(max_digits=5, decimal_places=2)
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

    def __str__(self):
        return f"{self.name} - ({self.event.name})"


class PackageOption(models.Model):
    package = models.ForeignKey(RacePackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    options_json = models.JSONField(null=True, blank=True) # changed to jsonfield.
    options_string = models.CharField(max_length=500, blank=True, null=True, editable=False)


    def set_options_from_string(self, options_string):
        """Converts a comma-separated string to a JSON array."""
        if options_string:
            options_list = [opt.strip() for opt in options_string.split(',')]
            self.options_json = [{"option": opt} for opt in options_list]
        else:
            self.options_json = None
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
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    hometown = models.CharField(max_length=100)
    race = models.ForeignKey("Race", on_delete=models.CASCADE)
    package = models.ForeignKey("RacePackage", on_delete=models.CASCADE)
    bib_number = models.CharField(max_length=10, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    selected_options = models.JSONField(default=dict, blank=True)  # Store selected options as JSON

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.race.race_type.name}"
