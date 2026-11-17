from django.urls import path

from . import views

app_name = "clubs"

urlpatterns = [
    path("", views.club_list, name="list"),
    path("my/", views.my_clubs, name="my_clubs"),
    path("<slug:slug>/", views.club_detail, name="detail"),
    path("<slug:slug>/join/", views.join_club, name="join"),
    path("<slug:slug>/leave/", views.leave_club, name="leave"),
    path("<slug:slug>/members/", views.manage_members, name="manage_members"),
    path(
        "<slug:slug>/members/<int:membership_id>/<str:action>/",
        views.update_membership,
        name="update_membership",
    ),
]
