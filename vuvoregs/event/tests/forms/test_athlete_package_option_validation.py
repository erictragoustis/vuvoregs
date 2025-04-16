import pytest
from django.http import QueryDict
from event.forms.athlete import AthleteForm
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.package_factory import RacePackageFactory


@pytest.mark.django_db
def test_missing_required_package_option_raises_error():
    """Should raise ValidationError if required package option is missing."""
    race = RaceFactory()
    package = RacePackageFactory(race=race)
    option = package.packageoption_set.create(
        name="T-shirt Size",
        options_json=["S", "M", "L"],
    )

    # Valid form fields but no option selected
    post = QueryDict("", mutable=True)
    post.update({
        "first_name": "Eva",
        "last_name": "Test",
        "email": "e@example.com",
        "phone": "123",
        "sex": "Female",
        "hometown": "Thessaloniki",
        "package": str(package.id),
        # Missing: athlete-0-option-{option.id}
        f"athlete-0-option-{option.id}-name": option.name,
    })

    form = AthleteForm(data=post, race=race)
    form.request = type("FakeRequest", (), {"POST": post})
    form.form_index = 0

    assert not form.is_valid()
    assert "Missing selections for: T-shirt Size" in str(form.errors)


@pytest.mark.django_db
def test_invalid_package_option_value_raises_error():
    """Should raise ValidationError if option value is invalid."""
    race = RaceFactory()
    package = RacePackageFactory(race=race)

    option = package.packageoption_set.create(
        name="T-shirt Size",
        options_json=["S", "M", "L"],
    )

    post = QueryDict("", mutable=True)
    post.update({
        "first_name": "Giannis",
        "last_name": "Invalid",
        "email": "giannis@pao.gr",
        "phone": "123456789",
        "sex": "Male",
        "hometown": "Athens",
        "package": str(package.id),
        f"athlete-0-option-{option.id}": "XXXL",  # 🚫 invalid value
        f"athlete-0-option-{option.id}-name": "T-shirt Size",
    })

    form = AthleteForm(data=post, race=race)
    form.request = type("FakeRequest", (), {"POST": post})
    form.form_index = 0

    is_valid = form.is_valid()

    # We want this test to FAIL validation
    assert not is_valid
    assert "T-shirt Size" in str(form.errors) or "Missing selections" in str(
        form.errors
    )
