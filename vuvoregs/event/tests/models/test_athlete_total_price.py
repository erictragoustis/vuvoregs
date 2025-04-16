from decimal import Decimal

import pytest

from event.tests.factories.athlete_factory import (
    AthleteFactory,
    RaceSpecialPriceFactory,
)
from event.tests.factories.package_factory import RacePackageFactory
from event.tests.factories.race_factory import RaceFactory
from event.tests.factories.registration_factory import RegistrationFactory
from event.tests.factories.time_based_price_factory import TimeBasedPriceFactory


@pytest.mark.django_db
def test_no_discount_with_few_athletes():
    """Should use individual price if team threshold is not met."""
    race = RaceFactory(
        base_price_individual=Decimal("30.00"),
        base_price_team=Decimal("20.00"),
        team_discount_threshold=3,
    )
    registration = RegistrationFactory(event=race.event)

    # Explicitly control package to remove adjustment
    package = RacePackageFactory(race=race, price_adjustment=Decimal("0.00"))

    # Only 2 athletes → no discount
    for _ in range(2):
        AthleteFactory(race=race, registration=registration, package=package)

    athlete = registration.athletes.first()
    assert athlete.get_total_price() == Decimal("30.00")


@pytest.mark.django_db
def test_team_discount_applies_with_enough_athletes():
    """Should use team price when enough athletes are registered."""
    race = RaceFactory(
        base_price_individual=Decimal("30.00"),
        base_price_team=Decimal("20.00"),
        team_discount_threshold=3,
    )
    registration = RegistrationFactory(event=race.event)

    package = RacePackageFactory(race=race, price_adjustment=Decimal("0.00"))

    # Add 3 athletes → meets threshold
    for _ in range(3):
        AthleteFactory(race=race, registration=registration, package=package)

    athlete = registration.athletes.first()
    assert athlete.get_total_price() == Decimal("20.00")


@pytest.mark.django_db
def test_total_price_includes_time_based_adjustment():
    """Should include time-based price if within the active window."""
    race = RaceFactory(
        base_price_individual=Decimal("30.00"), team_discount_threshold=None
    )
    registration = RegistrationFactory(event=race.event)
    package = RacePackageFactory(race=race, price_adjustment=Decimal("0.00"))

    TimeBasedPriceFactory(race=race, price_adjustment=Decimal("7.00"))

    athlete = AthleteFactory(race=race, registration=registration, package=package)

    assert athlete.get_total_price() == Decimal("37.00")


@pytest.mark.django_db
def test_total_price_applies_special_discount():
    """Should subtract special discount from base price."""
    race = RaceFactory(
        base_price_individual=Decimal("40.00"),
        base_price_team=Decimal("0.00"),
        team_discount_threshold=None,
    )
    registration = RegistrationFactory(event=race.event)
    package = RacePackageFactory(race=race, price_adjustment=Decimal("0.00"))

    special = RaceSpecialPriceFactory(race=race, discount_amount=Decimal("5.00"))

    athlete = AthleteFactory(
        race=race,
        registration=registration,
        package=package,
        special_price=special,
    )

    assert athlete.get_total_price() == Decimal("35.00")
