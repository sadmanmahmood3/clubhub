"""Main URL configuration for ClubHub.
Each app keeps its own urls.py; they are plugged in here."""
from django.contrib import admin
from django.urls import include, path

from accounts import views as account_views

admin.site.site_header = "ClubHub Administration"
admin.site.site_title = "ClubHub Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", account_views.home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("clubs/", include("clubs.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("notifications/", include("notifications.urls")),
]
