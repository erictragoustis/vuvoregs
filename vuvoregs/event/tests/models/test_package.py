import pytest
from decimal import Decimal
from event.tests.factories.package_factory import RacePackageFactory


@pytest.mark.django_db
def test_final_price_adds_adjustment_to_individual_base():
    package = RacePackageFactory(
        race__base_price_individual=Decimal("30.00"),
        price_adjustment=Decimal("5.00"),
    )

    assert package.get_final_price(is_team=False) == Decimal("35.00")


@pytest.mark.django_db
def test_final_price_adds_adjustment_to_team_base():
    package = RacePackageFactory(
        race__base_price_team=Decimal("25.00"),
        race__team_discount_threshold=3,
        price_adjustment=Decimal("5.00"),
    )

    assert package.get_final_price(is_team=True) == Decimal("30.00")


@pytest.mark.django_db
def test_final_price_ignores_team_flag_if_no_team_discount():
    package = RacePackageFactory(
        race__base_price_individual=Decimal("40.00"),
        race__base_price_team=Decimal("0.00"),
        race__team_discount_threshold=None,
        price_adjustment=Decimal("5.00"),
    )

    assert package.get_final_price(is_team=True) == Decimal("45.00")
