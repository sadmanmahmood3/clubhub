from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from clubs.models import Club, Membership
from events.models import Event

from .forms import ProfileForm, SignUpForm
from .models import User


def home(request):
    """Landing page: next few events and the most popular clubs."""
    upcoming_events = Event.objects.filter(
        status=Event.Status.APPROVED, start_time__gte=timezone.now()
    ).select_related("club")[:3]
    popular_clubs = Club.objects.filter(is_active=True).annotate(
        member_count=Count("memberships", filter=Q(memberships__status=Membership.Status.APPROVED))
    ).order_by("-member_count", "name")[:3]
    return render(request, "home.html", {
        "upcoming_events": upcoming_events,
        "popular_clubs": popular_clubs,
    })


def signup(request):
    """Create a new student account and log the student in."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ClubHub, {user.first_name}!")
            return redirect("accounts:dashboard")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    """One page that shows each user what matters to them."""
    user = request.user
    now = timezone.now()
    context = {
        "memberships": user.memberships.filter(
            status=Membership.Status.APPROVED
        ).select_related("club"),
        "pending_memberships": user.memberships.filter(
            status=Membership.Status.PENDING
        ).select_related("club"),
        "executive_clubs": Club.objects.filter(
            memberships__user=user,
            memberships__role=Membership.Role.EXECUTIVE,
            memberships__status=Membership.Status.APPROVED,
        ),
    }
    if user.is_dosa:
        context.update({
            "pending_event_count": Event.objects.filter(status=Event.Status.PENDING).count(),
            "upcoming_event_count": Event.objects.filter(
                status=Event.Status.APPROVED, start_time__gte=now
            ).count(),
            "club_count": Club.objects.filter(is_active=True).count(),
            "student_count": User.objects.filter(role=User.Role.STUDENT).count(),
        })
    return render(request, "accounts/dashboard.html", context)


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})
