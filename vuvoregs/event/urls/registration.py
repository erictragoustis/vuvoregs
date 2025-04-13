"""URL configuration for the registration module.

Includes routes for:
- Multi-athlete race registration
- T&Cs confirmation step
- Payment creation endpoint
"""

from django.urls import path

from event.views import (
    confirm_registration,
    create_payment,
    registration,
)

urlpatterns = [
    path(
        "race/<int:race_id>/register/",
        registration,
        name="registration",
    ),
    path(
        "registration/confirm/<int:registration_id>/",
        confirm_registration,
        name="confirm_registration",
    ),
    path(
        "registration/create-payment/<int:registration_id>/",
        create_payment,
        name="create_payment",
    ),
]
