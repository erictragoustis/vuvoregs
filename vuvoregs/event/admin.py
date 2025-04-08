from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.urls import path
from django_json_widget.widgets import JSONEditorWidget
import csv, io

from .models import (
    Event, TermsAndConditions, RaceType, Race, RacePackage, PackageOption,
    Registration, Athlete, PickUpPoint
)
from .forms import BibNumberImportForm, ExportEventAthletesForm

# 👤 Custom form with JSON widget
class AthleteAdminForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = '__all__'
        widgets = {
            'selected_options': JSONEditorWidget(options={'mode': 'form', 'mainMenuBar': True}),
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
            return "\n".join(f"{k}: {', '.join(v)}" for k, v in obj.selected_options.items())
        except Exception:
            return "⚠️ Invalid JSON"
    formatted_selected_options.short_description = "Selected Options"

@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ("event", "version", "created_at")
    search_fields = ("event__name", "version", "title")
    ordering = ("-created_at",)

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
    fields = ['package', 'name', 'options_string']
    readonly_fields = ['display_options']

    def display_options(self, obj):
        if not obj.options_json:
            return "-"
        return ", ".join(obj.options_json)
    display_options.short_description = "Parsed Options"

    def save_model(self, request, obj, form, change):
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

# ✅ CSV Export for athletes
@admin.action(description="📤 Export selected athletes to CSV")
def export_athletes_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=athletes_export.csv'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['id', 'first_name', 'last_name', 'email', 'phone', 'package', 'race', 'bib_number'])
    for athlete in queryset:
        writer.writerow([
            athlete.id, athlete.first_name, athlete.last_name, athlete.email, athlete.phone,
            athlete.package.name if athlete.package else '',
            athlete.race.name if athlete.race else '',
            athlete.bib_number or ''
        ])
    return response

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    form = AthleteAdminForm
    ordering = ['-registration__created_at']
    list_display = (
        'registration__created_at','first_name', 'last_name', 'email', 'race', 'package',
        'pickup_point', 'get_status', 'agreed_to_terms', 'formatted_selected_options'
    )
    list_filter = ('race__event', 'race', 'package', 'pickup_point')
    search_fields = ('first_name', 'last_name', 'race__name', 'email')
    readonly_fields = ['formatted_selected_options', 'agreed_to_terms']
    actions = [export_athletes_to_csv]

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

# ➕ Bonus: Add views manually (optional, requires URL config)
def import_bibs_view(request):
    form = BibNumberImportForm()
    success, failed = 0, 0
    if request.method == "POST":
        form = BibNumberImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['csv_file']
            reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'), delimiter=';')
            for row in reader:
                athlete_id = row.get('id')
                bib = row.get('bib_number')
                try:
                    athlete = Athlete.objects.get(id=athlete_id)
                    athlete.bib_number = bib
                    athlete.save()
                    success += 1
                except Athlete.DoesNotExist:
                    failed += 1
            messages.success(request, f"{success} bib numbers updated.")
            if failed:
                messages.warning(request, f"{failed} rows failed (no matching Athlete ID).")
            return redirect("admin:index")
    return render(request, "admin/import_bibs.html", {"form": form, "title": "Import Bib Numbers"})

def export_athletes_view(request):
    form = ExportEventAthletesForm()
    if request.method == 'POST':
        form = ExportEventAthletesForm(request.POST)
        if form.is_valid():
            event = form.cleaned_data['event']
            athletes = Athlete.objects.filter(race__event=event).select_related('package', 'race')
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename=athletes_{event.name or event.id}.csv'
            writer = csv.writer(response, delimiter=';')
            writer.writerow(['id', 'first_name', 'last_name', 'dob','package', 'race', 'pickup_point','bib_number'])
            for athlete in athletes:
                writer.writerow([
                    athlete.id, athlete.first_name, athlete.last_name, athlete.dob, athlete.pickup_point.name,
                    athlete.package.name if athlete.package else '',
                    athlete.race.name if athlete.race else '',
                    athlete.bib_number or ''
                ])
            return response
    return render(request, 'admin/export_athletes.html', {'form': form, 'title': "Export Event Athletes"})
