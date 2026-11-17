"""Main URL configuration for ClubHub.
Each app keeps its own urls.py; they are plugged in here."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

admin.site.site_header = "ClubHub Administration"
admin.site.site_title = "ClubHub Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
]
