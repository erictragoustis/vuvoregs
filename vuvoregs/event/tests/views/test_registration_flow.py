from django.urls import reverse
import pytest

from event.models import Athlete, Registration
from event.tests.factories.event import PickUpPointFactory
from event.tests.factories.race import RaceFactory
from event.tests.factories.race_package import RacePackageFactory
from event.tests.factories.terms import TermsFactory


@pytest.mark.django_db
def test_registration_get_renders_form(client):
    """GET request to registration page returns 200 and form context."""
    race = RaceFactory()
    url = reverse("event:register", args=[race.id])
    response = client.get(url)
    assert response.status_code == 200
    assert (
        b"Register" in response.content or b"registration" in response.content.lower()
    )


@pytest.mark.django_db
def test_registration_post_creates_registration_and_athletes(client):
    """POSTing valid data creates a registration and athletes."""
    race = RaceFactory(min_participants=2)
    package = RacePackageFactory(race=race, price=30)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)

    url = reverse("event:register", args=[race.id])

    post_data = {
        "athlete-TOTAL_FORMS": "2",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
    }

    for i in range(2):
        post_data.update({
            f"athlete-{i}-first_name": f"Test{i}",
            f"athlete-{i}-last_name": "User",
            f"athlete-{i}-email": f"user{i}@example.com",
            f"athlete-{i}-phone": "1234567890",
            f"athlete-{i}-dob": "1990-01-01",
            f"athlete-{i}-hometown": "City",
            f"athlete-{i}-package": str(package.id),
            f"athlete-{i}-pickup_point": str(pickup.id),
            f"athlete-{i}-agrees_to_terms": "on",
        })

    response = client.post(url, post_data, follow=True)
    assert response.status_code == 200

    # Check models created
    registration = Registration.objects.last()
    assert registration.race == race
    assert registration.total_amount == 2 * package.price
    assert registration.athletes.count() == 2

    names = list(registration.athletes.values_list("first_name", flat=True))
    assert "Test0" in names
    assert "Test1" in names


@pytest.mark.django_db
def test_registration_post_missing_terms_is_invalid(client):
    """Formset should reject submissions where terms are not agreed."""
    race = RaceFactory(min_participants=1)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)

    url = reverse("event:register", args=[race.id])

    post_data = {
        "athlete-TOTAL_FORMS": "1",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
        "athlete-0-first_name": "NoTerms",
        "athlete-0-last_name": "User",
        "athlete-0-email": "no@terms.com",
        "athlete-0-phone": "123456789",
        "athlete-0-dob": "1990-01-01",
        "athlete-0-hometown": "Nowhere",
        "athlete-0-package": str(package.id),
        "athlete-0-pickup_point": str(pickup.id),
        # Missing athlete-0-agrees_to_terms
    }

    response = client.post(url, post_data)
    assert response.status_code == 200
    assert b"agree" in response.content.lower() or b"terms" in response.content.lower()
    assert b"This field is required" in response.content


@pytest.mark.django_db
def test_registration_post_missing_package_is_invalid(client):
    """Formset should reject submissions with no package selected."""
    race = RaceFactory(min_participants=1)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)

    url = reverse("event:register", args=[race.id])

    post_data = {
        "athlete-TOTAL_FORMS": "1",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
        "athlete-0-first_name": "NoPackage",
        "athlete-0-last_name": "User",
        "athlete-0-email": "no@pkg.com",
        "athlete-0-phone": "123456789",
        "athlete-0-dob": "1990-01-01",
        "athlete-0-hometown": "Nowhere",
        "athlete-0-agrees_to_terms": "on",
        "athlete-0-pickup_point": str(pickup.id),
        # Missing athlete-0-package
    }

    response = client.post(url, post_data)
    assert response.status_code == 200
    assert b"This field is required" in response.content


@pytest.mark.django_db
def test_registration_post_not_enough_participants(client):
    """Should fail if number of athletes < race.min_participants."""
    race = RaceFactory(min_participants=3)
    package = RacePackageFactory(race=race)
    pickup = PickUpPointFactory(event=race.event)
    TermsFactory(event=race.event)

    url = reverse("event:register", args=[race.id])

    post_data = {
        "athlete-TOTAL_FORMS": "2",  # Need at least 3
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
    }

    for i in range(2):
        post_data.update({
            f"athlete-{i}-first_name": f"Short{i}",
            f"athlete-{i}-last_name": "Group",
            f"athlete-{i}-email": f"short{i}@mail.com",
            f"athlete-{i}-phone": "000111222",
            f"athlete-{i}-dob": "1995-05-05",
            f"athlete-{i}-hometown": "CityX",
            f"athlete-{i}-package": str(package.id),
            f"athlete-{i}-pickup_point": str(pickup.id),
            f"athlete-{i}-agrees_to_terms": "on",
        })

    response = client.post(url, post_data)
    assert response.status_code == 200
    assert (
        b"at least 3 participants" in response.content
        or b"formset" in response.content.lower()
    )
