from django.contrib import admin
from .models import Event, RaceType, Race, RacePackage, PackageOption, Registration, Athlete

class AthleteInline(admin.TabularInline):
    model = Athlete
    extra = 0  # Number of empty forms to display

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'location')

@admin.register(RaceType)
class RaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ('race_type', 'race_km', 'event')
    list_filter = ('event', 'race_type')
    search_fields = ('race_type__name', 'event__name')

@admin.register(RacePackage)
class RacePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price')
    list_filter = ('event',)
    search_fields = ('name', 'event__name')

@admin.register(PackageOption)
class PackageOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'package')
    list_filter = ('package',)
    search_fields = ('name', 'package__name')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('id',)
    inlines = [AthleteInline]

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'race', 'package', 'registration')
    list_filter = ('race', 'package')
    search_fields = ('first_name', 'last_name', 'race__name')