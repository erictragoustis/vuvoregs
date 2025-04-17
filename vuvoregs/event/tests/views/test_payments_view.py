from unittest.mock import patch

from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils import translation
import pytest
from requests.exceptions import HTTPError

from event.models import Payment
from event.tests.factories import (
    CityFactory,
    CountryFactory,
    PaymentFactory,
    RegionFactory,
    RegistrationFactory,
    TermsAndConditionsFactory,
)
from payments import RedirectNeeded


@pytest.mark.django_db
def test_payment_success_view(client):
    registration = RegistrationFactory()
    url = reverse("payment_success", args=[registration.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "registration" in response.context


@pytest.mark.django_db
def test_payment_failure_view(client):
    registration = RegistrationFactory()
    url = reverse("payment_failure", args=[registration.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "registration" in response.context


@pytest.mark.django_db
def test_create_payment_redirects_if_terms_not_agreed(client):
    registration = RegistrationFactory()
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    url = reverse("create_payment", args=[registration.id])
    response = client.post(url, data={"agrees_to_terms": "off"})

    assert response.status_code == 302
    assert reverse("confirm_registration", args=[registration.id]) in response.url


@pytest.mark.django_db
def test_create_payment_redirects_if_already_paid(client):
    registration = RegistrationFactory()
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    payment = PaymentFactory()
    registration.payment = payment
    registration.save(update_fields=["payment"])

    TermsAndConditionsFactory(event=registration.event)
    url = reverse("create_payment", args=[registration.id])

    with patch(
        "event.models.payment.Payment.get_form",
        side_effect=RedirectNeeded("/redirect-me"),
    ):
        response = client.post(url, data={"agrees_to_terms": "on"})

    assert response.status_code == 302
    assert response.url == "/redirect-me"


@pytest.mark.django_db
def test_create_payment_success_redirect(client):
    registration = RegistrationFactory(payment=None)
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    TermsAndConditionsFactory(event=registration.event)
    country = CountryFactory()
    region = RegionFactory(country=country)
    city = CityFactory(country=country, region=region)

    url = reverse("create_payment", args=[registration.id])
    data = {
        "agrees_to_terms": "on",
        "billing_first_name": "Test",
        "billing_last_name": "User",
        "billing_address_1": "123 Street",
        "billing_address_2": "Apt 4",
        "billing_postcode": "12345",
        "billing_country": str(country.id),
        "billing_region": str(region.id),
        "billing_city": str(city.id),
        "billing_phone": "1234567890",
        "billing_email": "test@example.com",
    }

    with patch(
        "event.models.payment.Payment.get_form", side_effect=RedirectNeeded("/to-viva")
    ):
        response = client.post(url, data=data)

    assert response.status_code == 302
    assert response.url == "/to-viva"


@pytest.mark.django_db
def test_create_payment_handles_http_error(client):
    registration = RegistrationFactory(payment=None)
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    TermsAndConditionsFactory(event=registration.event)
    country = CountryFactory()
    region = RegionFactory(country=country)
    city = CityFactory(country=country, region=region)

    url = reverse("create_payment", args=[registration.id])
    data = {
        "agrees_to_terms": "on",
        "billing_first_name": "Test",
        "billing_last_name": "User",
        "billing_address_1": "123 Street",
        "billing_address_2": "Apt 4",
        "billing_postcode": "12345",
        "billing_country": str(country.id),
        "billing_region": str(region.id),
        "billing_city": str(city.id),
        "billing_phone": "1234567890",
        "billing_email": "test@example.com",
    }

    with patch(
        "event.models.payment.Payment.get_form", side_effect=HTTPError("Viva error")
    ):
        response = client.post(url, data=data)

    assert response.status_code == 302
    assert reverse("confirm_registration", args=[registration.id]) in response.url


@pytest.mark.django_db
def test_create_payment_handles_generic_exception(client):
    registration = RegistrationFactory(payment=None)
    registration.total_amount = 10
    registration.save(update_fields=["total_amount"])

    TermsAndConditionsFactory(event=registration.event)
    country = CountryFactory()
    region = RegionFactory(country=country)
    city = CityFactory(country=country, region=region)

    url = reverse("create_payment", args=[registration.id])
    data = {
        "agrees_to_terms": "on",
        "billing_first_name": "Test",
        "billing_last_name": "User",
        "billing_address_1": "123 Street",
        "billing_address_2": "Apt 4",
        "billing_postcode": "12345",
        "billing_country": str(country.id),
        "billing_region": str(region.id),
        "billing_city": str(city.id),
        "billing_phone": "1234567890",
        "billing_email": "test@example.com",
    }

    with patch(
        "event.models.payment.Payment.get_form",
        side_effect=Exception("Unexpected error"),
    ):
        response = client.post(url, data=data)

    assert response.status_code == 302
    assert reverse("confirm_registration", args=[registration.id]) in response.url


@pytest.mark.django_db
def test_payment_success_view_renders(client):
    registration = RegistrationFactory()
    url = reverse("payment_success", args=[registration.id])

    response = client.get(url)

    assert response.status_code == 200
    assert "registration/payment_success.html" in [t.name for t in response.templates]
    assert response.context["registration"] == registration


@pytest.mark.django_db
def test_payment_failure_view_renders(client):
    registration = RegistrationFactory()
    url = reverse("payment_failure", args=[registration.id])

    response = client.get(url)

    assert response.status_code == 200
    assert "registration/payment_failure.html" in [t.name for t in response.templates]
    assert response.context["registration"] == registration


@pytest.mark.django_db
def test_viva_success_redirect_handler_redirects():
    url = reverse("viva_success_redirect_handler")
    response = Client().get(url + "?t=TX123")

    assert response.status_code == 302
    assert "/payment/success/TX123/" in response.url


def test_viva_success_redirect_handler_missing_param():
    url = reverse("viva_success_redirect_handler")
    response = Client().get(url)

    assert response.status_code == 400
    assert "Missing transaction ID" in response.content.decode()


@pytest.mark.django_db
def test_check_transaction_status_not_found(client):
    url = reverse("check_transaction_status", args=["UNKNOWN"])
    response = client.get(url)
    assert response.json()["status"] == "not_found"


@pytest.mark.django_db
def test_check_transaction_status_confirmed(client):
    registration = RegistrationFactory()
    payment = PaymentFactory(status="confirmed", transaction_id="TX00001")
    registration.payment = payment
    registration.save(update_fields=["payment"])

    url = reverse("check_transaction_status", args=["TX00001"])
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert "/payment/" in response.json()["redirect_url"]


@pytest.mark.django_db
def test_check_transaction_status_waiting(client):
    payment = PaymentFactory(status="waiting")
    url = reverse("check_transaction_status", args=[payment.transaction_id])

    response = client.get(url)
    assert response.json()["status"] == "waiting"
