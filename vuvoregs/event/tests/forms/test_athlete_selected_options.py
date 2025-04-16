import pytest
from django.http import QueryDict
from event.forms.athlete import AthleteForm
from event.tests.factories.athlete_factory import AthleteFactory
from event.tests.factories.package_factory import RacePackageFactory
from event.tests.factories.race_factory import RaceFactory


@pytest.mark.django_db
def test_selected_options_are_parsed_correctly():
    """Should parse POSTed dynamic options into selected_options dict."""
    race = RaceFactory()
    package = RacePackageFactory(race=race)
    option_name = "T-shirt Size"

    # Add one PackageOption manually
    option = package.packageoption_set.create(
        name=option_name,
        options_json=["S", "M", "L"],
    )

    form_data = {
        "first_name": "Alex",
        "last_name": "Test",
        "email": "a@example.com",
        "phone": "123",
        "sex": "Male",
        "hometown": "Athens",
        "package": str(package.id),
    }

    # Simulate POST keys like athlete-0-option-<id>
    post = QueryDict("", mutable=True)
    post.update(form_data)
    post.update({
        f"athlete-0-option-{option.id}": "M",
        f"athlete-0-option-{option.id}-name": option_name,
    })

    form = AthleteForm(data=post, race=race)
    form.request = type("FakeRequest", (), {"POST": post})
    form.form_index = 0

    assert form.is_valid()
    selected = form.instance.selected_options
    assert isinstance(selected, dict)
    assert selected == {option_name: ["M"]}
