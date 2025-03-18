from django.contrib import admin
from .models import Event, RaceType, Race, RacePackage, Athlete, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    search_fields = ('name',)


@admin.register(RaceType)
class RaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ('event', 'race_type', 'race_km')
    list_filter = ('event', 'race_type')
    search_fields = ('race_type__name', 'event__name')


@admin.register(RacePackage)
class RacePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'race', 'price')
    list_filter = ('race',)
    search_fields = ('name', 'race__race_type__name')


class AthleteInline(admin.TabularInline):
    model = Athlete
    extra = 0  

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'status', 'total_amount', 'payment_status')
    list_filter = ('status', 'payment_status')
    ordering = ('-created_at',)
    inlines = [AthleteInline]

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'registration', 'race', 'package', 'bib_number', 'email')
    list_filter = ('race', 'package', 'sex')
    search_fields = ('first_name', 'last_name', 'email', 'bib_number')
   
