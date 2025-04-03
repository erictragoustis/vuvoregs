from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('event/<int:event_id>/races/', views.race_list, name='race_list'),
    path('race/<int:race_id>/register/', views.registration, name='registration'),
    path('race/package/<int:package_id>/options/', views.package_options, name='package_options'),
    path('payment/<int:registration_id>/', views.payment, name='payment'),
    path('payment/<int:registration_id>/success/', views.payment_success, name='payment_success'),
    path('payment/<int:registration_id>/failure/', views.payment_failure, name='payment_failure'),
]