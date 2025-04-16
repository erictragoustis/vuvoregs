import pytest
from event.models import Race
from event.tests.factories.race import RaceFactory


@pytest.mark.django_db
def test_race_creation_with_event_and_type():
    """Test that a Race links correctly to an Event and RaceType."""
    race = RaceFactory(race_type__min_participants=1)
    assert race.event is not None
    assert race.race_type is not None
    assert isinstance(race.race_km, int)
    assert race.min_participants >= 1


@pytest.mark.django_db
def test_race_str_method():
    """Test string representation of Race."""
    race = RaceFactory(name="Ultra Run")
    assert str(race) == "Ultra Run"
