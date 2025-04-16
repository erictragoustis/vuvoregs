from django.forms import inlineformset_factory
import factory
import pytest

from event.forms.athlete import AthleteForm, MinParticipantsFormSet
from event.models import Athlete, Registration
from event.tests.factories.athlete_factory import AthleteFactory
from event.tests.factories.package_factory import RacePackageFactory
from event.tests.factories.race_factory import RaceFactory, RaceRoleFactory
from event.tests.factories.registration_factory import RegistrationFactory


@pytest.mark.django_db
def test_min_participants_validation_fails_if_not_enough_athletes():
    """Should raise ValidationError if race requires more participants than provided."""
    race = RaceFactory(race_type__min_participants=2)
    registration = RegistrationFactory(event=race.event)

    FormSet = inlineformset_factory(
        parent_model=Registration,
        model=Athlete,
        form=AthleteForm,
        formset=MinParticipantsFormSet,
        extra=2,
        can_delete=False,
    )

    # Simulate one filled form, one blank
    form_data = {
        "athlete-TOTAL_FORMS": "2",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "2",
        "athlete-0-first_name": "Nick",
        "athlete-0-last_name": "Calathes",
        "athlete-0-email": "nick@greens.gr",
        "athlete-0-phone": "123456",
        "athlete-0-sex": "Male",
        "athlete-0-hometown": "Athens",
        "athlete-0-package": "",
        "athlete-1-first_name": "",  # blank form
        "athlete-1-last_name": "",
    }

    formset = FormSet(
        data=form_data,
        instance=registration,
        form_kwargs={"race": race},
    )
    formset.race = race

    assert not formset.is_valid()
    assert "requires at least 2 participants" in str(formset.non_form_errors())


@pytest.mark.django_db
def test_missing_required_roles_raises_validation_error():
    """Should raise ValidationError if required roles are not all present."""
    role_runner = RaceRoleFactory(name="Runner")
    role_cyclist = RaceRoleFactory(name="Cyclist")

    race = RaceFactory(
        race_type__min_participants=2,
        race_type__roles=[role_runner, role_cyclist],
    )
    registration = RegistrationFactory(event=race.event)
    package = RacePackageFactory(race=race, price_adjustment=0)

    FormSet = inlineformset_factory(
        parent_model=Registration,
        model=Athlete,
        form=AthleteForm,
        formset=MinParticipantsFormSet,
        extra=2,
        can_delete=False,
    )

    form_data = {
        "athlete-TOTAL_FORMS": "2",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "2",
        # Athlete 0 → valid with role
        "athlete-0-first_name": "Runner",
        "athlete-0-last_name": "Guy",
        "athlete-0-email": "run@gr.com",
        "athlete-0-phone": "123",
        "athlete-0-sex": "Male",
        "athlete-0-hometown": "Athens",
        "athlete-0-package": str(package.id),
        "athlete-0-role": str(role_runner.id),
        # Athlete 1 → valid, but no role assigned
        "athlete-1-first_name": "Unassigned",
        "athlete-1-last_name": "Person",
        "athlete-1-email": "un@gr.com",
        "athlete-1-phone": "123456",
        "athlete-1-sex": "Male",
        "athlete-1-hometown": "Athens",
        "athlete-1-package": str(package.id),
        "athlete-1-role": "",  # ✅
        # deliberately missing role
    }

    formset = FormSet(
        data=form_data,
        instance=registration,
        form_kwargs={"race": race},
        race=race,
    )

    # 💡 Inject request + form_index manually for proper option logic
    fake_request = type("FakeRequest", (), {"POST": form_data})
    formset.request = fake_request
    for i, form in enumerate(formset.forms):
        form.request = fake_request
        form.form_index = i

    assert not formset.is_valid()
    print("non_form_errors:", formset.non_form_errors())
    assert "The following roles must be assigned" in str(formset.non_form_errors())
