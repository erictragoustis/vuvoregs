import pytest
from decimal import Decimal
from event.tests.factories.race_factory import RaceFactory


@pytest.mark.django_db
def test_individual_price_returns_correct_base():
    """Should return individual base price when not a team registration."""
    race = RaceFactory(
        base_price_individual=Decimal("25.00"),
        base_price_team=Decimal("15.00"),
        team_discount_threshold=3,
    )

    assert race.get_effective_base_price(is_team=False) == Decimal("25.00")


@pytest.mark.django_db
def test_team_price_returns_discounted_base():
    """Should return team base price if discount is enabled and team flag is set."""
    race = RaceFactory(
        base_price_individual=Decimal("25.00"),
        base_price_team=Decimal("15.00"),
        team_discount_threshold=3,
    )

    assert race.get_effective_base_price(is_team=True) == Decimal("15.00")


@pytest.mark.django_db
def test_team_price_falls_back_to_individual_if_no_discount():
    """Should return individual price if team discount is not configured."""
    race = RaceFactory(
        base_price_individual=Decimal("25.00"),
        base_price_team=Decimal("0.00"),
        team_discount_threshold=None,
    )

    assert race.get_effective_base_price(is_team=True) == Decimal("25.00")
