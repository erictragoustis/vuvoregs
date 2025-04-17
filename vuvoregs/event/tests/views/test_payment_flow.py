from cities_light.models import City, Country, Region
from django.urls import reverse
import pytest

from event.models import TermsAndConditions
from event.tests.factories.registration_factory import RegistrationFactory
from payments import RedirectNeeded


@pytest.mark.django_db
def test_payment_creation_requires_terms_agreement(client):
    """Should block payment creation if user didn't check the box."""
    registration = RegistrationFactory()
    event = registration.event
    TermsAndConditions.objects.create(
        event=event, version="1.0", title="T&Cs", content="..."
    )

    url = reverse("create_payment", args=[registration.id])
    response = client.post(url, data={}, follow=True)

    assert b"You must agree to the Terms" in response.content
    registration.refresh_from_db()
    assert not registration.agrees_to_terms
    assert registration.payment is None


@pytest.mark.django_db
def test_payment_created_and_linked(client, monkeypatch):
    """Should create payment and redirect to Viva checkout."""
    registration = RegistrationFactory()
    event = registration.event
    TermsAndConditions.objects.create(
        event=event, version="1.0", title="T&Cs", content="..."
    )

    country = Country.objects.create(name="Greece", code2="GR")
    region = Region.objects.create(name="Attica", country=country)
    city = City.objects.create(name="Athens", region=region, country=country)

    # ✅ Raise RedirectNeeded instead of generic Exception
    def fake_get_form(self):
        raise RedirectNeeded("https://fake-checkout.com")

    from event.models.payment import Payment

    monkeypatch.setattr(Payment, "get_form", fake_get_form)

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

    response = client.post(url, data=post_data)

    registration.refresh_from_db()
    payment = registration.payment

    assert response.status_code == 302
    assert response["Location"] == "https://fake-checkout.com"
    assert registration.agrees_to_terms is True
    assert registration.agreed_to_terms == event.terms
    assert payment is not None
    assert payment.registration == registration
    assert payment.total == registration.total_amount
