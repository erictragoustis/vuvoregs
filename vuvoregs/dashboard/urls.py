from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('registrations/', views.registration_list, name='registrations'),
    path('event/<int:event_id>/', views.event_dashboard, name='event_dashboard'),
    path('event/<int:event_id>/chart-data/', views.event_chart_data, name='event_chart_data'),
]
