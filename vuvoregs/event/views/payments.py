"""Viva Wallet integration views.

Handles:
- Redirection flow after checkout
- Webhook processing (payment success/failure)
- Transaction polling via AJAX
"""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from event.models import Payment
from payments import PaymentStatus


def viva_success_redirect_handler(request):
    """Intermediate view that handles ?t=<transaction_id> redirects from Viva Wallet.

    Redirects to our internal success endpoint.
    """
    transaction_id = request.GET.get("t")
    if not transaction_id:
        return HttpResponse("Missing transaction ID", status=400)

    return redirect("viva_payment_success", transaction_id=transaction_id)


def viva_payment_success(request, transaction_id):
    """Final success handler after a confirmed payment.

    - Marks payment and registration as confirmed if not already
    - If payment is not found yet (due to webhook delay), show 'pending' state
    - Redirects to regular success view
    """
    transaction_id = transaction_id.strip()

    payment = Payment.objects.filter(transaction_id__iexact=transaction_id).first()

    if not payment:
        return render(
            request,
            "registration/payment_pending.html",
            {"transaction_id": transaction_id},
            status=202,
        )

    registration = getattr(payment, "registration", None)

    if payment.status != PaymentStatus.CONFIRMED:
        payment.status = PaymentStatus.CONFIRMED
        payment.save(update_fields=["status"])

        if registration:
            registration.payment_status = "paid"
            registration.status = "completed"
            registration.save(update_fields=["payment_status", "status"])

    return redirect("payment_success", registration_id=registration.id)


def viva_payment_failure(request, transaction_id):
    """Handler for failed/cancelled Viva Wallet payments.

    - Marks payment + registration as failed if not already
    - Redirects to payment_failure view
    """
    payment = get_object_or_404(Payment, transaction_id=transaction_id)
    registration = getattr(payment, "registration", None)

    if not registration:
        return HttpResponse(
            "Payment found but not linked to any registration.",
            status=500,
        )

    if payment.status != PaymentStatus.ERROR:
        payment.status = PaymentStatus.ERROR
        payment.save(update_fields=["status"])

        registration.payment_status = "failed"
        registration.status = "failed"
        registration.save(update_fields=["payment_status", "status"])

    return redirect("payment_failure", registration_id=registration.id)


logger = logging.getLogger(__name__)


@csrf_exempt
def payment_webhook(request):
    """Viva Wallet webhook listener.

    Handles payment success (1796) and failure (1798) notifications.

    Payload structure:
        {
            "EventTypeId": 1796,
            "EventData": {
                "TransactionId": "...",
                "OrderCode": "..."
            }
        }

    Returns:
        JsonResponse
    """
    logger.debug("Received request body: %s", request.body)
    if request.method == "GET":
        return JsonResponse({"Key": settings.VIVA_WEBHOOK_VERIFICATION_KEY})
    try:
        payload = json.loads(request.body)
        event_type_id = payload.get("EventTypeId")
        transaction_data = payload.get("EventData", {})
        transaction_id = transaction_data.get("TransactionId")
        order_code = transaction_data.get("OrderCode")
        if settings.DEBUG:
            print("📬 Webhook received:", event_type_id, transaction_id)

        payment = Payment.objects.filter(order_code=str(order_code)).first()
        if not payment:
            return JsonResponse(
                {"status": "error", "message": "Payment not found"},
                status=404,
            )

        registration = getattr(payment, "registration", None)

        # Save transaction ID if not already present

        payment.transaction_id = transaction_id
        payment.save(update_fields=["transaction_id"])

        if event_type_id == 1796:  # Payment successful
            payment.status = PaymentStatus.CONFIRMED
            payment.save(update_fields=["status"])

            if registration:
                registration.status = "completed"
                registration.payment_status = "paid"
                registration.save(update_fields=["status", "payment_status"])

        elif event_type_id == 1798:  # Payment failed
            payment.status = PaymentStatus.ERROR
            payment.save(update_fields=["status"])

            if registration:
                registration.status = "failed"
                registration.payment_status = "failed"
                registration.save(update_fields=["status", "payment_status"])
        logger.debug("Parsed JSON payload: %s", payload)
        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.error("Error parsing JSON: %s", str(e))
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500,
        )


@require_GET
def check_transaction_status(request, transaction_id):
    """AJAX endpoint to check status of a given Viva Wallet transaction.

    Used when a webhook might not have yet updated the UI.

    Returns:
        - "confirmed" + redirect URL if paid
        - "waiting" if still pending
        - "not_found" if unknown transaction
    """
    payment = Payment.objects.filter(transaction_id=transaction_id).first()

    if not payment:
        return JsonResponse({"status": "not_found"})

    if payment.status == PaymentStatus.CONFIRMED:
        return JsonResponse({
            "status": "confirmed",
            "redirect_url": f"/payment/{payment.registration.id}/success/",
        })

    return JsonResponse({"status": "waiting"})
