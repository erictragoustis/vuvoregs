from django.contrib import admin
from .models import Event, RaceType, Race, RacePackages

# Register your models here.

admin.site.register(Event)
admin.site.register(RaceType)
admin.site.register(Race)
admin.site.register(RacePackages)