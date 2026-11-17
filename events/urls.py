from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("<int:pk>/", views.event_detail, name="detail"),
    path("<int:pk>/edit/", views.event_edit, name="edit"),
    path("<int:pk>/submit/", views.submit_for_approval, name="submit"),
    path("club/<slug:slug>/", views.club_events, name="club_events"),
    path("club/<slug:slug>/new/", views.event_create, name="create"),
]
