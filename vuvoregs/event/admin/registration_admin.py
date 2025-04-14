from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from event.models.registration import Registration
from event.models.athlete import Athlete


class AthleteInline(admin.TabularInline):
    model = Athlete
    extra = 0
    readonly_fields = ["formatted_selected_options"]
    fields = [
        "first_name",
        "last_name",
        "email",
        "package",
        "race",
        "formatted_selected_options",
    ]

    def formatted_selected_options(self, obj):
        if not obj.selected_options:
            return "-"
        try:
            return "\n".join(
                f"{k}: {', '.join(v)}" for k, v in obj.selected_options.items()
            )
        except Exception:
            return "⚠️ Invalid JSON"

    formatted_selected_options.short_description = "Selected Options"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "created_at",
        "status",
        "payment_status",
        "total_amount",
        "num_athletes",
        "get_terms_version",
        "agrees_to_terms",
        "payment_link",
    )
    list_filter = ("event", "status", "payment_status", "agrees_to_terms")
    search_fields = ("id", "event__name")
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "total_amount",
        "get_terms_version",
        "num_athletes",
        "payment_link",
    )
    inlines = [AthleteInline]

    @admin.display(description="T&Cs Version")
    def get_terms_version(self, obj):
        return obj.agreed_to_terms.version if obj.agreed_to_terms else "—"

    @admin.display(description="Athletes")
    def num_athletes(self, obj):
        return obj.athletes.count()

    @admin.display(description="Payment")
    def payment_link(self, obj):
        if obj.payment:
            url = reverse("admin:event_payment_change", args=[obj.payment.id])
            return format_html(
                '<a href="{}">#{} – {}</a>', url, obj.payment.id, obj.payment.status
            )
        return "—"
