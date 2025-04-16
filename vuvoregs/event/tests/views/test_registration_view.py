import pytest
from django.urls import reverse
from event.tests.factories.race import RaceFactory
from event.tests.factories.race_package import RacePackageFactory
from event.tests.factories.event import PickUpPointFactory
from event.tests.factories.terms import TermsFactory
from event.models import RaceSpecialPrice, Registration, Athlete


@pytest.mark.django_db
def test_registration_post_with_special_price(client):
    """Simulate registration form POST with special price selected."""
    race = RaceFactory(race_type__min_participants=1)
    package = RacePackageFactory(race=race, price=50)
    pickup = PickUpPointFactory(event=race.event)
    terms = TermsFactory(event=race.event)

    special = RaceSpecialPrice.objects.create(
        race=race,
        name="Student Discount",
        discount_amount=15,
        show_on_registration=True,
    )

    url = reverse("event:register", args=[race.id])
    post_data = {
        # formset mgmt
        "athlete-TOTAL_FORMS": "1",
        "athlete-INITIAL_FORMS": "0",
        "athlete-MIN_NUM_FORMS": "0",
        "athlete-MAX_NUM_FORMS": "1000",
        # athlete 0
        "athlete-0-first_name": "John",
        "athlete-0-last_name": "Doe",
        "athlete-0-email": "john@example.com",
        "athlete-0-phone": "1234567890",
        "athlete-0-dob": "1990-01-01",
        "athlete-0-hometown": "Athens",
        "athlete-0-package": package.id,
        "athlete-0-pickup_point": pickup.id,
        "athlete-0-agrees_to_terms": "on",
        # selected special price
        "selected_special_price": str(special.id),
    }

    response = client.post(url, data=post_data, follow=True)

    # Check registration created
    registration = Registration.objects.last()
    assert registration is not None
    assert registration.race == race

    # Check athlete created
    athlete = Athlete.objects.last()
    assert athlete.registration == registration
    assert athlete.first_name == "John"

    # Final price should reflect discount
    expected_price = package.price - special.discount_amount
    assert registration.total_amount == expected_price

    # Optional: check redirect or success message
    assert response.status_code == 200
