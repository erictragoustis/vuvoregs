import pytest
from event.models import RaceSpecialPrice
from event.tests.factories.race import RaceFactory
from event.tests.factories.race_package import RacePackageFactory


@pytest.mark.django_db
def test_race_package_returns_base_price():
    """If no special prices apply, get_final_price returns base price."""
    pkg = RacePackageFactory(price=40)
    assert pkg.get_final_price() == 40


@pytest.mark.django_db
def test_race_package_applies_special_price():
    """get_final_price should subtract special price discount if present."""
    race = RaceFactory()
    pkg = RacePackageFactory(race=race, price=50)

    # Attach a special price
    RaceSpecialPrice.objects.create(
        race=race,
        name="Student Discount",
        discount_amount=10,
        show_on_registration=True,
    )

    # With 1 active special price, the logic should apply discount
    assert pkg.get_final_price() == 40
