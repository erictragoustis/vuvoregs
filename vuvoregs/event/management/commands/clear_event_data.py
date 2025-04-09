from django.core.management.base import BaseCommand

from event.models import (
    Athlete,
    Event,
    PackageOption,
    Payment,
    PickUpPoint,
    Race,
    RacePackage,
    Registration,
    TermsAndConditions,
)


class Command(BaseCommand):
    help = "Delete all seeded event, registration, and payment data."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⚠️ Deleting all event-related data..."))

        models = [
            Payment, Athlete, Registration,
            PackageOption, RacePackage, Race,
            TermsAndConditions, PickUpPoint, Event
        ]

        for model in models:
            deleted_count, _ = model.objects.all().delete()
            self.stdout.write(f"Deleted {deleted_count} from {model.__name__}")

        self.stdout.write(self.style.SUCCESS("✅ All event-related data deleted."))