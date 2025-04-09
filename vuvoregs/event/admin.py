# 🔧 Core Python imports
import csv
import io
import json

from django import forms
from django.conf import settings

# 🧩 Django core admin functionality
from django.contrib import admin, messages

# 🌐 HTTP, routing, and utilities
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.test import RequestFactory
from django.urls import reverse

# 🧱 Third-party widgets
from django_json_widget.widgets import JSONEditorWidget

from .forms import BibNumberImportForm, ExportEventAthletesForm

# 📦 Local app models and forms
from .models import (
    Athlete,
    Event,
    PackageOption,
    PackageSpecialPrice,
    Payment,
    PickUpPoint,
    Race,
    RacePackage,
    RaceType,
    Registration,
    TermsAndConditions,
)


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
        'registration__created_at', 'first_name', 'last_name', 'email', 'race', 'package',
        'pickup_point', 'get_status', 'special_price_option', 'agreed_to_terms', 'formatted_selected_options'
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
            writer.writerow(['id', 'first_name', 'last_name', 'dob', 'package', 'race', 'pickup_point', 'bib_number'])
            for athlete in athletes:
                writer.writerow([
                    athlete.id, athlete.first_name, athlete.last_name, athlete.dob, athlete.pickup_point.name,
                    athlete.package.name if athlete.package else '',
                    athlete.race.name if athlete.race else '',
                    athlete.bib_number or ''
                ])
            return response
    return render(request, 'admin/export_athletes.html', {'form': form, 'title': "Export Event Athletes"})


@admin.action(description="Set payment status to 'confirmed'")
def simulate_success(modeladmin, request, queryset):
    for payment in queryset:
        payment.status = 'confirmed'
        payment.save()
        if hasattr(payment, 'registration'):
            registration = payment.registration
            registration.status = 'completed'
            registration.payment_status = 'paid'
            registration.save()


@admin.action(description="Set payment status to 'failed'")
def simulate_failure(modeladmin, request, queryset):
    for payment in queryset:
        payment.status = 'rejected'
        payment.save()
        if hasattr(payment, 'registration'):
            registration = payment.registration
            registration.status = 'failed'
            registration.payment_status = 'failed'
            registration.save()


@admin.action(description="🚀 Simulate Webhook for selected payments")
@admin.action(description="🚀 Simulate Webhook for selected payments")
def simulate_webhook(modeladmin, request, queryset):
    from .views import payment_webhook

    # ✅ Only allow if DEBUG=True
    if not settings.DEBUG:
        messages.error(request, "❌ This action is only available in development mode.")
        return

    factory = RequestFactory()

    for payment in queryset:
        data = json.dumps({'payment_id': str(payment.id)})
        simulated_request = factory.post(
            reverse('payment_webhook'),
            data=data,
            content_type='application/json'
        )
        response = payment_webhook(simulated_request)
        if isinstance(response, JsonResponse) and response.status_code == 200:
            messages.success(request, f"✅ Webhook simulated for payment #{payment.id}")
        else:
            messages.error(request, f"❌ Webhook failed for payment #{payment.id}")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'variant',
        'status',
        'total',
        'currency',
        'billing_email',
        'created',
        'modified',
    )
    list_filter = ('variant', 'status', 'currency')
    search_fields = ('billing_email', 'id', 'extra_data')
    readonly_fields = ('created', 'modified', 'captured_amount')
    actions = [simulate_success, simulate_failure, simulate_webhook]
    

@admin.register(PackageSpecialPrice)
class PackageSpecialPriceAdmin(admin.ModelAdmin):
    list_display = ('label', 'package', 'event', 'race', 'price')
    list_filter = ('package__event', 'package', 'event', 'race')
    search_fields = ('label', 'package__name', 'event__name', 'race__name')
    ordering = ('package', 'label')
    
    
