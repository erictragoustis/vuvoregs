"""View layer responsible for managing the full registration flow, including.

- Displaying upcoming events and associated races
- Handling multi-athlete race registration forms
- Dynamically providing package and pricing options via AJAX
- Integrating payment workflows (creation, confirmation, failure handling)
- Responding to webhooks and verifying payment statuses

This module orchestrates core interactions between athletes,
events, and the payment system.
"""

# Built-in libraries
import json

# Django core imports
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

# Local app imports
from event.models import (
    Payment,
)

# Third-party packages
from payments import PaymentStatus


def viva_success_redirect_handler(request):
    transaction_id = request.GET.get("t")
    if not transaction_id:
        return HttpResponse("Missing transaction ID", status=400)

    return redirect("viva_payment_success", transaction_id=transaction_id)


def viva_payment_success(request, transaction_id):
    transaction_id = transaction_id.strip()
    print("🔎 Looking for payment with transaction_id:", transaction_id)

    payment = Payment.objects.filter(transaction_id__iexact=transaction_id).first()

    if not payment:
        # Fallback if webhook hasn't saved it yet
        return render(
            request,
            "registration/payment_pending.html",
            {"transaction_id": transaction_id},
            status=202,
        )

    registration = getattr(payment, "registration", None)

    if payment.status != PaymentStatus.CONFIRMED:
        payment.status = PaymentStatus.CONFIRMED
        payment.save()

        if registration:
            registration.payment_status = "paid"
            registration.status = "completed"
            registration.save()

    return redirect("payment_success", registration_id=registration.id)


def viva_payment_failure(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id)
    registration = getattr(payment, "registration", None)
    if not registration:
        return HttpResponse(
            "Payment found but not linked to any registration.", status=500
        )

    if payment.status != PaymentStatus.ERROR:
        payment.status = PaymentStatus.ERROR
        payment.save()

        if registration:
            registration.payment_status = "failed"
            registration.status = "failed"
            registration.save()

    return redirect("payment_failure", registration_id=registration.id)


@csrf_exempt
def payment_webhook(request):
    try:
        payload = json.loads(request.body)
        event_type_id = payload.get("EventTypeId")
        transaction_data = payload.get("EventData", {})
        transaction_id = transaction_data.get("TransactionId")
        order_code = transaction_data.get("OrderCode")

        print("📬 Webhook received:", event_type_id, transaction_id)

        # ✅ Lookup by order_code, not transaction_id
        payment = Payment.objects.filter(order_code=str(order_code)).first()
        if not payment:
            return JsonResponse(
                {"status": "error", "message": "Payment not found"}, status=404
            )

        registration = getattr(payment, "registration", None)

        # ✅ Save the real transaction_id
        if not payment.transaction_id:
            payment.transaction_id = transaction_id
            payment.save(update_fields=["transaction_id"])

        if event_type_id == 1796:  # Payment successful
            payment.status = PaymentStatus.CONFIRMED
            payment.save()

            if registration:
                registration.status = "completed"
                registration.payment_status = "paid"
                registration.save()

        elif event_type_id == 1798:  # Payment failed
            payment.status = PaymentStatus.ERROR
            payment.save()

            if registration:
                registration.status = "failed"
                registration.payment_status = "failed"
                registration.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_GET
def check_transaction_status(request, transaction_id):
    payment = Payment.objects.filter(transaction_id=transaction_id).first()

    if not payment:
        return JsonResponse({"status": "not_found"})

    if payment.status == PaymentStatus.CONFIRMED:
        return JsonResponse({
            "status": "confirmed",
            "redirect_url": f"/payment/{payment.registration.id}/success/",
        })

    return JsonResponse({"status": "waiting"})
