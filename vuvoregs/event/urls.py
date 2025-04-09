"""URL configuration for the event module.

This module defines URL patterns for handling event-related views, including
event lists, race registrations, payment processing, and special price options.
"""

from django.urls import include, path

from . import views

urlpatterns = [
    # 📅 List all events (homepage)
    path('', views.event_list, name='event_list'),

    # 🏁 Show races under a selected event
    path('event/<int:event_id>/races/', 
         views.race_list, name='race_list'),

    # 📝 Register athletes for a race
    path('race/<int:race_id>/register/', 
         views.registration, name='registration'),

    # 📦 AJAX: Fetch options for a selected race package
    path('race/package/<int:package_id>/options/', 
         views.package_options, name='package_options'),

    # 💳 Manual check: fetch payment status from provider
    path('registration/<int:registration_id>/check-payment/', 
         views.check_payment_status, name='check_payment_status'),

    # 🔁 Payment provider URLs (handled by django-payments)
    path('payments/', 
         include('payments.urls')),  # 🌐 Handles provider redirects (success/fail) 

    # 🔔 Webhook: receives payment status updates from the gateway
    path('payments/webhook/', 
         views.payment_webhook, name='payment_webhook'),

    # ✅ Payment success screen
    path('payment/<int:registration_id>/success/', 
         views.payment_success, name='payment_success'),

    # ❌ Payment failure screen
    path('payment/<int:registration_id>/failure/', 
         views.payment_failure, name='payment_failure'),

    # 🎯 Return special pricing options for a package (AJAX)
    path("race/package/<int:package_id>/special-prices/", 
         views.special_price_options, name="special_price_options"),

    # 📄 Review registration data before payment
    path('registration/confirm/<int:registration_id>/', 
         views.confirm_registration, name='confirm_registration'),

    # 💳 Create payment object + redirect to payment gateway
    path('registration/create-payment/<int:registration_id>/', 
         views.create_payment, name='create_payment'),
]
