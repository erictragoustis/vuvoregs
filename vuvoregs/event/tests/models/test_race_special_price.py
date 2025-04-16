import pytest
from event.models import RaceSpecialPrice
from event.tests.factories.race import RaceFactory


@pytest.mark.django_db
def test_race_special_price_creation_and_str():
    """Basic creation of a special price with correct string format."""
    race = RaceFactory()
    special = RaceSpecialPrice.objects.create(
        race=race, name="Early Bird", discount_amount=15, show_on_registration=True
    )

    assert str(special) == "Early Bird (-15€)"
    assert special.race == race
