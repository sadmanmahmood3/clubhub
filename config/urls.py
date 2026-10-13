"""Main URL configuration for ClubHub.
Each app keeps its own urls.py; they are plugged in here."""
from django.contrib import admin
from django.urls import path

admin.site.site_header = "ClubHub Administration"
admin.site.site_title = "ClubHub Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
]
