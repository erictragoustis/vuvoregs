from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class CustomUserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'full_name', 'is_organizer', 'is_athlete', 'is_guest', 'is_staff')
    list_filter = ('is_organizer', 'is_athlete', 'is_guest', 'is_staff', 'is_superuser')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'date_of_birth')}),
        ('Roles', {'fields': ('is_organizer', 'is_athlete', 'is_guest')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_organizer', 'is_athlete', 'is_guest')}
        ),
    )


admin.site.register(User, CustomUserAdmin)
