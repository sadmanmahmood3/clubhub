from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "start_time", "venue", "capacity", "status")
    list_filter = ("status", "club")
    search_fields = ("title", "description", "venue")
    date_hierarchy = "start_time"
    readonly_fields = ("created_at", "updated_at", "reviewed_at")
