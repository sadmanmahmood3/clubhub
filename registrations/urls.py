from django.urls import path

from . import views

app_name = "registrations"

urlpatterns = [
    path("", views.my_registrations, name="my_registrations"),
    path("report/", views.participation_report, name="report"),
    path("event/<int:event_id>/register/", views.register, name="register"),
    path("event/<int:event_id>/cancel/", views.cancel_registration, name="cancel"),
    path("event/<int:event_id>/list/", views.event_registrations, name="event_registrations"),
    path("event/<int:event_id>/checkin/", views.checkin, name="checkin"),
    path("event/<int:event_id>/code/", views.generate_checkin_code, name="generate_code"),
    path("event/<int:event_id>/export/", views.export_attendance, name="export"),
]
