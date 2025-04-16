import pytest
from django.http import QueryDict
from event.forms import AthleteForm
from event.tests.factories.race import RaceFactory
from event.tests.factories.race_package import RacePackageFactory
from event.tests.factories.event import PickUpPointFactory
from event.tests.factories.terms import TermsFactory


@pytest.mark.django_db
def test_athlete_form_requires_package_and_terms():
    """Form should error if package or T&Cs not agreed."""
    race = RaceFactory(race_type__min_participants=1)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)  # required for form setup

    form = AthleteForm(
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "12345678",
            "dob": "1990-01-01",
            "hometown": "City",
            "pickup_point": pickup.pk,
            # ❌ package + terms missing
        },
        race=race,
        packages=[package],
    )

    assert not form.is_valid()
    assert "package" in form.errors
    assert "agrees_to_terms" in form.errors


@pytest.mark.django_db
def test_athlete_form_valid_with_terms_and_package(client):
    """Form should validate when terms and package are present."""
    race = RaceFactory(race_type__min_participants=1)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)

    post_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "12345678",
        "dob": "1990-01-01",
        "hometown": "City",
        "pickup_point": pickup.pk,
        "package": package.pk,
        "agrees_to_terms": "on",
        # simulate selected_options via request.POST
        "athlete-0-option-1": "Red",
        "athlete-0-option-1-name": "T-Shirt",
    }

    form = AthleteForm(
        data=post_data,
        race=race,
        packages=[package],
    )

    # Inject request + index for option parsing
    form.request = type("Request", (), {"POST": QueryDict("", mutable=True)})
    form.request.POST.update(post_data)
    form.form_index = 0

    assert form.is_valid()
    instance = form.save(commit=False)
    assert "T-Shirt" in instance.selected_options
