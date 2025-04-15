"""Admin actions and configurations for managing Payment objects.

This module provides:
- Admin actions to simulate payment success, failure, and webhook events.
- PaymentAdmin class for customizing the Django admin interface for Payment objects.
"""

import json

from django.conf import settings
from django.contrib import admin, messages
from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from event.models.payment import Payment
from event.views import payment_webhook


@admin.action(description="Set payment status to 'confirmed'")
def simulate_success(modeladmin, request, queryset):
    """Set the status of selected payments to 'confirmed' and update registrations.

    Parameters
    ----------
    modeladmin : ModelAdmin
        The admin interface for the model.
    request : HttpRequest
        The HTTP request object.
    queryset : QuerySet
        The selected Payment objects to update.
    """
    for payment in queryset:
        payment.status = "confirmed"
        payment.save()
        if hasattr(payment, "registration"):
            registration = payment.registration
            registration.status = "completed"
            registration.payment_status = "paid"
            registration.save()


@admin.action(description="Set payment status to 'failed'")
def simulate_failure(modeladmin, request, queryset):
    """Set the status of selected payments to 'rejected' and update  registrations.

    Parameters
    ----------
    modeladmin : ModelAdmin
        The admin interface for the model.
    request : HttpRequest
        The HTTP request object.
    queryset : QuerySet
        The selected Payment objects to update.
    """
    for payment in queryset:
        payment.status = "rejected"
        payment.save()
        if hasattr(payment, "registration"):
            registration = payment.registration
            registration.status = "failed"
            registration.payment_status = "failed"
            registration.save()


@admin.action(description="🚀 Simulate Webhook for selected payments")
def simulate_webhook(modeladmin, request, queryset):
    """Simulate a webhook event for the selected payments.

    Parameters
    ----------
    modeladmin : ModelAdmin
        The admin interface for the model.
    request : HttpRequest
        The HTTP request object.
    queryset : QuerySet
        The selected Payment objects to simulate the webhook for.
    """
    if not settings.DEBUG:
        messages.error(request, "❌ This action is only available in development mode.")
        return

    factory = RequestFactory()
    for payment in queryset:
        data = json.dumps({"payment_id": str(payment.id)})
        simulated_request = factory.post(
            reverse("payment_webhook"), data=data, content_type="application/json"
        )
        response = payment_webhook(simulated_request)
        if isinstance(response, JsonResponse) and response.status_code == 200:
            messages.success(request, f"✅ Webhook simulated for payment #{payment.id}")
        else:
            messages.error(request, f"❌ Webhook failed for payment #{payment.id}")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for managing Payment objects.

    This class customizes the Django admin interface for Payment objects,
    providing list display, filters, search fields, and custom actions.
    """

    list_display = (
        "id",
        "variant",
        "status",
        "total",
        "order_code",
        "currency",
        "billing_email",
        "created",
        "modified",
    )
    list_filter = ("variant", "status", "currency")
    search_fields = ("billing_email", "id", "extra_data")
    readonly_fields = ("created", "modified", "captured_amount")
    actions = [simulate_success, simulate_failure, simulate_webhook]
