from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ClubHubUserAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "student_id", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "student_id", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("ClubHub", {"fields": ("role", "student_id", "department", "phone")}),
    )
