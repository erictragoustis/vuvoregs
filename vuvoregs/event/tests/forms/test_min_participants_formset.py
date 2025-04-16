import pytest
from django.forms import inlineformset_factory
from event.forms import athlete_formset_factory
from event.tests.factories.race import RaceFactory
from event.tests.factories.registration import RegistrationFactory
from event.tests.factories.athlete import AthleteFactory
from event.tests.factories.race_package import RacePackageFactory
from event.tests.factories.event import PickUpPointFactory
from event.tests.factories.terms import TermsFactory


@pytest.mark.django_db
def test_formset_requires_minimum_participants():
    """Formset should raise ValidationError if min_participants is not met."""
    race = RaceFactory(min_participants=2)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)
    registration = RegistrationFactory(race=race)

    # only one form submitted (but two required)
    formset_data = {
        "athlete-TOTAL_FORMS": "1",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
        "athlete-0-first_name": "Alice",
        "athlete-0-last_name": "Doe",
        "athlete-0-email": "alice@example.com",
        "athlete-0-phone": "123456789",
        "athlete-0-hometown": "City",
        "athlete-0-dob": "1990-01-01",
        "athlete-0-package": str(package.id),
        "athlete-0-pickup_point": str(pickup.id),
        "athlete-0-agrees_to_terms": "on",
    }

    AthleteFormSet = athlete_formset_factory(race)
    formset = AthleteFormSet(
        data=formset_data,
        race=race,
        form_kwargs={"race": race, "packages": [package]},
        prefix="athlete",
    )
    formset.request = type("Request", (), {"POST": formset_data})

    assert not formset.is_valid()
    assert formset.non_form_errors()
    assert "at least 2 participants" in formset.non_form_errors()[0]


@pytest.mark.django_db
def test_formset_passes_with_required_number_of_forms():
    """Formset should pass if min_participants is met or exceeded."""
    race = RaceFactory(min_participants=2)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)
    registration = RegistrationFactory(race=race)

    formset_data = {
        "athlete-TOTAL_FORMS": "2",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
    }

    for i in range(2):
        formset_data.update({
            f"athlete-{i}-first_name": f"User{i}",
            f"athlete-{i}-last_name": "Doe",
            f"athlete-{i}-email": f"user{i}@test.com",
            f"athlete-{i}-phone": "9999999999",
            f"athlete-{i}-hometown": "Townsville",
            f"athlete-{i}-dob": "1990-01-01",
            f"athlete-{i}-package": str(package.id),
            f"athlete-{i}-pickup_point": str(pickup.id),
            f"athlete-{i}-agrees_to_terms": "on",
        })

    AthleteFormSet = athlete_formset_factory(race)
    formset = AthleteFormSet(
        data=formset_data,
        race=race,
        form_kwargs={"race": race, "packages": [package]},
        prefix="athlete",
    )
    formset.request = type("Request", (), {"POST": formset_data})

    assert formset.is_valid()
