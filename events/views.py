from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import dosa_required
from notifications.utils import notify

from clubs.models import Club, Membership

from .forms import EventForm, ReviewForm
from .models import Event


def event_list(request):
    """Public list of approved events that have not ended yet."""
    query = request.GET.get("q", "").strip()
    club_slug = request.GET.get("club", "")

    events = Event.objects.filter(
        status=Event.Status.APPROVED, end_time__gte=timezone.now()
    ).select_related("club")
    if query:
        events = events.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(venue__icontains=query)
        )
    if club_slug:
        events = events.filter(club__slug=club_slug)

    return render(request, "events/event_list.html", {
        "events": events,
        "query": query,
        "club_slug": club_slug,
        "clubs": Club.objects.filter(is_active=True),
    })


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.select_related("club", "created_by"), pk=pk)
    is_executive = event.club.is_executive(request.user)
    is_dosa = request.user.is_authenticated and request.user.is_dosa

    # Drafts, pending and rejected events are only visible to the club and DOSA
    if event.status not in (Event.Status.APPROVED, Event.Status.COMPLETED):
        if not (is_executive or is_dosa):
            raise Http404("Event not found")

    return render(request, "events/event_detail.html", {
        "event": event,
        "is_executive": is_executive,
    })


def _require_executive(request, club):
    if not club.is_executive(request.user):
        raise PermissionDenied("Only this club's executives can manage its events.")


@login_required
def event_create(request, slug):
    club = get_object_or_404(Club, slug=slug, is_active=True)
    _require_executive(request, club)

    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.club = club
        event.created_by = request.user
        event.save()
        messages.success(request, "Event saved as a draft. Submit it to DOSA when it is ready.")
        return redirect("events:detail", pk=event.pk)

    return render(request, "events/event_form.html", {"form": form, "club": club})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    _require_executive(request, event.club)
    if not event.can_be_edited:
        messages.error(request, "Only draft or rejected events can be edited.")
        return redirect("events:detail", pk=event.pk)

    form = EventForm(request.POST or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect("events:detail", pk=event.pk)

    return render(request, "events/event_form.html", {"form": form, "club": event.club, "event": event})


@login_required
@require_POST
def submit_for_approval(request, pk):
    """The club sends a draft (or a fixed, rejected event) to DOSA."""
    event = get_object_or_404(Event, pk=pk)
    _require_executive(request, event.club)
    if not event.can_be_edited:
        messages.error(request, "This event has already been sent to DOSA.")
        return redirect("events:detail", pk=event.pk)

    event.status = Event.Status.PENDING
    event.save(update_fields=["status", "updated_at"])
    messages.success(request, "Event sent to DOSA for approval.")

    User = get_user_model()
    dosa_users = User.objects.filter(Q(role=User.Role.DOSA) | Q(is_superuser=True))
    notify(
        dosa_users,
        f"New event waiting for approval: {event.title} ({event.club.name}).",
        reverse("events:review", args=[event.pk]),
    )
    return redirect("events:detail", pk=event.pk)


@login_required
def club_events(request, slug):
    """All events of one club (including drafts), for its executives."""
    club = get_object_or_404(Club, slug=slug)
    _require_executive(request, club)
    events = club.events.order_by("-start_time")
    return render(request, "events/club_events.html", {"club": club, "events": events})


# ---------------------------------------------------------------- DOSA approval

@dosa_required
def approval_queue(request):
    pending = Event.objects.filter(status=Event.Status.PENDING).select_related(
        "club", "created_by"
    ).order_by("updated_at")
    recently_reviewed = Event.objects.filter(reviewed_at__isnull=False).select_related(
        "club", "reviewed_by"
    ).order_by("-reviewed_at")[:10]
    return render(request, "events/approval_queue.html", {
        "pending": pending,
        "recently_reviewed": recently_reviewed,
    })


@dosa_required
def review_event(request, pk):
    """DOSA approves or rejects one pending event, with a comment."""
    event = get_object_or_404(Event.objects.select_related("club", "created_by"), pk=pk)
    if event.status != Event.Status.PENDING:
        messages.info(request, "This event is not waiting for approval.")
        return redirect("events:approval_queue")

    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        approved = form.cleaned_data["decision"] == ReviewForm.APPROVE
        event.status = Event.Status.APPROVED if approved else Event.Status.REJECTED
        event.dosa_comment = form.cleaned_data["comment"]
        event.reviewed_by = request.user
        event.reviewed_at = timezone.now()
        event.save()

        executives = [m.user for m in event.club.memberships.filter(
            role=Membership.Role.EXECUTIVE, status=Membership.Status.APPROVED
        ).select_related("user")]
        result = "approved" if approved else "rejected"
        notify(executives, f"DOSA {result} your event \"{event.title}\".",
               reverse("events:detail", args=[event.pk]))

        messages.success(request, f"\"{event.title}\" was {result}.")
        return redirect("events:approval_queue")

    return render(request, "events/review_event.html", {"event": event, "form": form})


@login_required
@require_POST
def mark_completed(request, pk):
    event = get_object_or_404(Event, pk=pk)
    _require_executive(request, event.club)
    if event.status == Event.Status.APPROVED and event.has_ended:
        event.status = Event.Status.COMPLETED
        event.save(update_fields=["status", "updated_at"])
        messages.success(request, "Event marked as completed.")
    else:
        messages.error(request, "Only approved events that have ended can be completed.")
    return redirect("events:detail", pk=event.pk)
