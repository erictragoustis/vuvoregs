# event/urls_admin.py
from django.urls import path
from .admin import import_bibs_view, export_athletes_view

app_name = 'event_admin'

urlpatterns = [
    path('import-bibs/', import_bibs_view, name='import-bibs'),
    path('export-athletes/', export_athletes_view, name='export-athletes'),
]