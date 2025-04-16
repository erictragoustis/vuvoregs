import pytest
from event.models import Athlete
from event.tests.factories.athlete import AthleteFactory


@pytest.mark.django_db
def test_athlete_created_with_terms_and_options():
    """Athlete should have agreed terms and non-empty selected_options."""
    athlete = AthleteFactory()
    assert athlete.agreed_to_terms is not None
    assert athlete.selected_options
    assert isinstance(athlete.selected_options, dict)


@pytest.mark.django_db
def test_athlete_str_format():
    """Test string representation of Athlete."""
    athlete = AthleteFactory(first_name="Eric", last_name="Tragoustis")
    assert str(athlete) == "Eric Tragoustis"
