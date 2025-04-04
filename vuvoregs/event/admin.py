from django.contrib import admin
from .models import Event, RaceType, Race, RacePackage, PackageOption, Registration, Athlete, PickUpPoint
import json
from django import forms
from django_json_widget.widgets import JSONEditorWidget


class AthleteAdminForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = '__all__'
        widgets = {
            'selected_options': JSONEditorWidget(options={
                'mode': 'form',  # or 'code' or 'tree'
                'mainMenuBar': True,
            }),
        }

# 👥 Inline for displaying athletes under registrations
class AthleteInline(admin.TabularInline):
    model = Athlete
    extra = 0
    readonly_fields = ['formatted_selected_options']
    fields = ['first_name', 'last_name', 'email', 'package', 'race', 'formatted_selected_options']

    def formatted_selected_options(self, obj):
        if not obj.selected_options:
            return "-"
        try:
            options = obj.selected_options
            return "\n".join(f"{k}: {', '.join(v)}" for k, v in options.items())
        except Exception:
            return "⚠️ Invalid JSON"

    formatted_selected_options.short_description = "Selected Options"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'location')
    ordering = ('-date',)


@admin.register(RaceType)
class RaceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'race_type', 'race_km', 'event')
    list_filter = ('event', 'race_type')
    search_fields = ('race_type__name', 'event__name')
    ordering = ('event', 'race_type')


@admin.register(RacePackage)
class RacePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price')
    list_filter = ('event',)
    search_fields = ('name', 'event__name')
    ordering = ('event', 'name')


@admin.register(PackageOption)
class PackageOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'package', 'display_options')
    list_filter = ('package',)
    search_fields = ('name', 'package__name')
    fields = ['package', 'name', 'options_string']  # Editable field
    readonly_fields = ['display_options']  # Optional: for admin clarity

    def display_options(self, obj):
        """Read-only view of parsed options"""
        if not obj.options_json:
            return "-"
        return ", ".join(obj.options_json)

    display_options.short_description = "Parsed Options"

    def save_model(self, request, obj, form, change):
        """
        Override to automatically sync JSON on save.
        """
        obj.set_options_from_string(obj.options_string)
        super().save_model(request, obj, form, change)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('id',)
    ordering = ('-created_at',)
    inlines = [AthleteInline]



@admin.register(PickUpPoint)
class PickUpPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'address', 'working_hours')
    list_filter = ('event',)
    search_fields = ('name', 'address', 'event__name')

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    form = AthleteAdminForm  # ✅ Use custom form with JSON widget

    list_display = (
        'first_name', 'last_name', 'email', 'race', 'package','pickup_point', 'get_status', 'formatted_selected_options'
    )
    list_filter = ('race', 'package','pickup_point')
    search_fields = ('first_name', 'last_name', 'race__name', 'email')
    readonly_fields = ['formatted_selected_options']

    def get_status(self, obj):
        return obj.registration.status if obj.registration else '-'
    get_status.short_description = "Registration Status"

    def formatted_selected_options(self, obj):
        if not obj.selected_options:
            return "-"
        try:
            return "\n".join(f"{k}: {', '.join(v)}" for k, v in obj.selected_options.items())
        except Exception:
            return "⚠️ Invalid JSON"
    formatted_selected_options.short_description = "Package Options"

