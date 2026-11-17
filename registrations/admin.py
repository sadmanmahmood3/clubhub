from django.contrib import admin

from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "checked_in", "registered_at")
    list_filter = ("status", "checked_in", "event__club")
    search_fields = ("user__username", "user__student_id", "event__title")
