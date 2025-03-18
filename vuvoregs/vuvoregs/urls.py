from django.conf import settings
from django.conf.urls.static import static
"""
URL configuration for vuvoregs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from event.views import event_selection
from event import views

urlpatterns = [
    path('admin', admin.site.urls),
    path('', views.event_selection, name='event_selection'),
    path('races/<int:event_id>/', views.race_selection, name='race_selection'),
    path('packages/<int:race_id>/', views.package_selection, name='package_selection'),
    path('register/<int:package_id>/', views.athlete_registration, name='athlete_registration'),
    path('payment/<int:registration_id>/', views.payment_view, name='payment'),  # <-- Payment URL
    path('payment-success/', views.payment_success, name='payment_success'),  # <-- Payment Success URL
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]

if settings.DEBUG:
    urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)