import pytest
from django.urls import reverse
from event.models import Athlete, Registration
from event.tests.factories.event_factory import EventFactory
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.package_factory import RacePackageFactory


@pytest.mark.django_db
def test_valid_athlete_formset_creates_registration(client):
    event = EventFactory()
    race = RaceFactory(event=event, race_type__min_participants=2)
    package = RacePackageFactory(race=race, price_adjustment=5)

    url = reverse("registration", args=[race.id])

    form_data = {
        "athlete-TOTAL_FORMS": "2",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
        # Athlete 1
        "athlete-0-first_name": "Anna",
        "athlete-0-last_name": "Runner",
        "athlete-0-email": "anna@example.com",
        "athlete-0-phone": "123456789",
        "athlete-0-sex": "Female",
        "athlete-0-hometown": "Athens",
        "athlete-0-package": str(package.id),
        # Athlete 2
        "athlete-1-first_name": "Maria",
        "athlete-1-last_name": "Runner",
        "athlete-1-email": "maria@example.com",
        "athlete-1-phone": "987654321",
        "athlete-1-sex": "Female",
        "athlete-1-hometown": "Athens",
        "athlete-1-package": str(package.id),
    }

    response = client.post(url, data=form_data, follow=False)

    assert response.status_code == 302  # redirect to confirm
    registration = Registration.objects.first()
    athletes = Athlete.objects.filter(registration=registration)

    assert registration is not None
    assert athletes.count() == 2
    assert registration.total_amount > 0
    assert response["Location"].endswith(
        reverse("confirm_registration", args=[registration.id])
    )
