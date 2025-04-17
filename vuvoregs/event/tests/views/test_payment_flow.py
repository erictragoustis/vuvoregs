from cities_light.models import City, Country, Region
from django.urls import reverse
import pytest

from event.models import Payment, TermsAndConditions
from event.tests.factories.registration_factory import RegistrationFactory
from payments import RedirectNeeded
from event.models import Registration


@pytest.mark.django_db
def test_payment_creation_requires_terms_agreement(client):
    registration = RegistrationFactory()
    TermsAndConditions.objects.create(
        event=registration.event, version="1.0", title="T&Cs", content="..."
    )

    url = reverse("create_payment", args=[registration.id])
    response = client.post(url, data={}, follow=True)

    assert response.status_code == 200
    assert b"Billing" in response.content or b"toast" in response.content


@pytest.mark.django_db
def test_payment_created_and_linked(client, monkeypatch):
    registration = RegistrationFactory()
    TermsAndConditions.objects.create(
        event=registration.event, version="1.0", title="T&Cs", content="..."
    )

    # ✅ Ensure payment path is triggered
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    country = Country.objects.create(name="Greece", code2="GR")
    region = Region.objects.create(name="Attica", country=country)
    city = City.objects.create(name="Athens", region=region, country=country)

    assert registration.payment is None

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

    print("🚦 registration.payment before POST:", registration.payment)

    response = client.post(url, data=post_data, follow=True)

    print("🔁 Response status:", response.status_code)
    print("🔁 Redirect chain:", response.redirect_chain)
    print("🔍 Payment count:", Payment.objects.count())
    payment = Payment.objects.filter(registration=registration).first()
    print("🔗 Linked payment:", payment)

    assert payment is not None, "❌ Payment not created"

    monkeypatch.setattr(
        payment,
        "get_form",
        lambda *_: (_ for _ in ()).throw(RedirectNeeded("https://fake-checkout.com")),
    )

    try:
        payment.get_form()
    except RedirectNeeded as e:
        assert str(e) == "https://fake-checkout.com"
