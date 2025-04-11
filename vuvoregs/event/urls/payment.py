"""URL configuration for payment-related views in the event application.

This module defines URL patterns for handling payment status checks,
success and failure callbacks, and webhook integrations.
"""

from django.urls import include, path

from event.views import (
    check_payment_status,
    check_transaction_status,
    payment_failure,
    payment_success,
    payment_webhook,
    viva_payment_failure,
    viva_payment_success,
    viva_success_redirect_handler,
)

urlpatterns = [
    path(
        "registration/<int:registration_id>/check-payment/",
        check_payment_status,
        name="check_payment_status",
    ),
    path("payments/", include("payments.urls")),
    path("payments/webhook/", payment_webhook, name="payment_webhook"),
    path(
        "payment/<int:registration_id>/success/",
        payment_success,
        name="payment_success",
    ),
    path(
        "payment/<int:registration_id>/failure/",
        payment_failure,
        name="payment_failure",
    ),
    path(
        "payment/success/<str:transaction_id>/",
        viva_payment_success,
        name="viva_payment_success",
    ),
    path(
        "payment/failure/<str:transaction_id>/",
        viva_payment_failure,
        name="viva_payment_failure",
    ),
    path("payment/success/", viva_success_redirect_handler),
    path(
        "payment/check-status/<str:transaction_id>/",
        check_transaction_status,
        name="check_transaction_status",
    ),
]
