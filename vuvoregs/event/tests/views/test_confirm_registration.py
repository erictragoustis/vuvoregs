import pytest
from django.urls import reverse
from event.models import TermsAndConditions
from event.tests.factories.registration_factory import RegistrationFactory


@pytest.mark.django_db
def test_confirm_registration_requires_terms_agreement(client):
    """Should block submission if 'agree to terms' is not checked."""
    registration = RegistrationFactory()
    event = registration.event

    # Add linked Terms & Conditions
    terms = TermsAndConditions.objects.create(
        event=event, version="1.0", title="T&Cs", content="..."
    )

    response = client.post(
        reverse("confirm_registration", args=[registration.id]),
        data={},  # no checkbox
        follow=True,
    )

    registration.refresh_from_db()

    assert response.status_code == 200
    assert registration.agrees_to_terms is False
    assert registration.agreed_to_terms is None


@pytest.mark.django_db
def test_confirm_registration_saves_terms_and_redirects(client):
    """Should store terms agreement and redirect when box is checked."""
    registration = RegistrationFactory()
    event = registration.event
    terms = TermsAndConditions.objects.create(
        event=event, version="1.0", title="T&Cs", content="..."
    )

    response = client.post(
        reverse("confirm_registration", args=[registration.id]),
        data={"agrees_to_terms": "on"},
        follow=False,
    )

    registration.refresh_from_db()
    assert registration.agrees_to_terms is True
    assert registration.agreed_to_terms == terms
    assert response.status_code == 302  # redirect to payment creation
    assert reverse("create_payment", args=[registration.id]) in response["Location"]
