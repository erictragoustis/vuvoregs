import pytest
from event.tests.factories import RaceFactory, RacePackageFactory


@pytest.mark.django_db
def test_package_final_price():
    package = RacePackageFactory(price_adjustment=10)
    race = package.race
    price = package.get_final_price(is_team=False)
    assert price == race.base_price_individual + 10
