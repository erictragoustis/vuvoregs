import pytest
from django.http import QueryDict
from event.forms.athlete import AthleteForm
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.package_factory import RacePackageFactory
from event.tests.factories.pickup_point_factory import PickupPointFactory


@pytest.mark.django_db
def test_selected_options_are_parsed_correctly():
    """Should parse POSTed dynamic options into selected_options dict."""
    race = RaceFactory()
    package = RacePackageFactory(race=race)
    option_name = "T-shirt Size"

    option = package.packageoption_set.create(
        name=option_name,
        options_json=["S", "M", "L"],
    )

    pickup = PickupPointFactory(event=race.event)

    form_data = {
        "first_name": "Alex",
        "last_name": "Test",
        "email": "a@example.com",
        "phone": "1234567890",
        "sex": "Male",
        "dob": "2000-01-01",
        "hometown": "Athens",
        "pickup_point": str(pickup.id),
        "package": str(package.id),
    }

    post = QueryDict("", mutable=True)
    post.update({f"athlete-0-{k}": v for k, v in form_data.items()})
    post.update({
        f"athlete-0-option-{option.id}": "M",
        f"athlete-0-option-{option.id}-name": option.name,
    })

    form = AthleteForm(data=post, race=race, prefix="athlete-0")
    form.setRequestAndIndex(request=type("FakeRequest", (), {"POST": post}), index=0)

    assert form.is_valid(), form.errors
    assert form.instance.selected_options == {option_name: ["M"]}
