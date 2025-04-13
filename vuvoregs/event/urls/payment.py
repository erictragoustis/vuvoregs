"""URL configuration for payment-related views in the event application.

Includes:
- Registration payment creation and success/failure views
- Viva Wallet success/failure callbacks
- AJAX status checks
- Webhook endpoint for payment provider events
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
    # Manual status check for internal use
    path(
        "registration/<int:registration_id>/check-payment/",
        check_payment_status,
        name="check_payment_status",
    ),
    # Standard django-payments URLs (e.g. success, cancel, error hooks)
    path("payments/", include("payments.urls")),
    # Webhook endpoint (used by Viva to confirm status asynchronously)
    path("payments/webhook/", payment_webhook, name="payment_webhook"),
    # Payment flow success/failure via registration ID
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
    # Viva Wallet callbacks (via transaction ID)
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
    path(
        "payment/success/",
        viva_success_redirect_handler,
        name="viva_success_redirect_handler",
    ),
    # AJAX polling: check transaction status via frontend polling
    path(
        "payment/check-status/<str:transaction_id>/",
        check_transaction_status,
        name="check_transaction_status",
    ),
]
