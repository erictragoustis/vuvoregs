from django.core.management.base import BaseCommand
from event.models import (
    Athlete, Registration, Race, Event,
    RacePackage, PackageOption, PickUpPoint, TermsAndConditions
)


class Command(BaseCommand):
    help = "🚨 DANGER: Deletes all event-related data. Keeps users and unrelated models safe."

    def handle(self, *args, **kwargs):
        models = [
            Athlete, Registration, RacePackage, PackageOption,
            PickUpPoint, TermsAndConditions, Race, Event
        ]

        for model in models:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"🗑️ Deleted {count} from {model.__name__}"))

        self.stdout.write(self.style.SUCCESS("✅ All event-related data cleared."))
