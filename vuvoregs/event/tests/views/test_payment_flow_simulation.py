import pytest
from django.urls import reverse
from django.utils import translation

from cities_light.models import Country, Region, City
from event.tests.factories import EventFactory, RegistrationFactory
from event.models import TermsAndConditions


@pytest.mark.django_db
def test_viva_checkout_redirect_flow(client):
    """
    Simulates full Smart Checkout redirection from billing form.
    This assumes get_form() triggers a RedirectNeeded with a fake URL.
    """
    # Setup valid country/region/city for billing info
    country = Country.objects.create(name="Greece", code2="GR")
    region = Region.objects.create(name="Attica", country=country)
    city = City.objects.create(name="Athens", region=region, country=country)

    # Create Event and Registration
    event = EventFactory(name="Test Event")
    registration = RegistrationFactory(event=event, total_amount=25)

    # Manually create and link terms
    terms = TermsAndConditions.objects.create(
        event=event, version="1.0", title="Test Terms", content="Terms body"
    )
    event.terms = terms
    event.save()

    url = reverse("create_payment", args=[registration.id])
    post_data = {
        "agrees_to_terms": "on",
        "billing_first_name": "Test",
        "billing_last_name": "User",
        "billing_address_1": "123 Street",
        "billing_address_2": "Apartment 3B",
        "billing_postcode": "11111",
        "billing_country": str(country.id),
        "billing_region": str(region.id),
        "billing_city": str(city.id),
        "billing_phone": "1234567890",
        "billing_email": "test@example.com",
    }

    # Use translation override for i18n URLs if needed
    with translation.override("en"):
        response = client.post(url, data=post_data, follow=False)
    # Simulate what would happen next, for example, follow redirection, etc.

    assert response.status_code in (302, 303)  # Should redirect to Viva Smart Checkout

    # You can also check for a location header, etc.
    # assert response["Location"].startswith("https://...")
