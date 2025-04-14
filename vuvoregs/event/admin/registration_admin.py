from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from event.models.athlete import Athlete
from event.models.registration import Registration


class AthleteInline(admin.TabularInline):
    """Inline admin interface for managing Athlete objects within a Registration.

    This class allows the display and editing of Athlete details directly
    from the Registration admin interface.
    """

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
        """Format and return the selected options for an athlete.

        Parameters
        ----------
        obj : Athlete
            The athlete instance whose selected options are to be formatted.

        Returns
        -------
        str
            A formatted string of selected options or a placeholder if none exist.
        """
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
    """Admin interface for managing Registration objects.

    This class provides a detailed interface for viewing, filtering, and
    managing registrations, including related athletes and payment details.
    """

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
        """Retrieve the terms and conditions version agreed to by the registrant.

        Parameters
        ----------
        obj : Registration
            The registration instance for which the terms version is retrieved.

        Returns,
        -------
        str
            The version of the agreed terms and conditions, or "—" if not available.
        """
        return obj.agreed_to_terms.version if obj.agreed_to_terms else "—"

    @admin.display(description="Athletes")
    def num_athletes(self, obj):
        """Retrieve the number of athletes associated with a registration.

        Parameters
        ----------
        obj : Registration
            The registration instance for which the athlete count is retrieved.

        Returns,
        -------
        int
            The number of athletes linked to the registration.
        """
        return obj.athletes.count()

    @admin.display(description="Payment")
    def payment_link(self, obj):
        """Generate a link to the payment details for the registration.

        Parameters
        ----------
        obj : Registration
            The registration instance for which the payment link is generated.

        Returns
        -------
        str
            An HTML link to the payment details if a payment exists, or "—" if not.
        """
        if obj.payment:
            url = reverse("admin:event_payment_change", args=[obj.payment.id])
            return format_html(
                '<a href="{}">#{} – {}</a>', url, obj.payment.id, obj.payment.status
            )
        return "—"
