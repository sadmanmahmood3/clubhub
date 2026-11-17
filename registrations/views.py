import csv
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from accounts.decorators import dosa_required
from clubs.models import Club
from events.models import Event

from .models import Registration
from .services import active_registrations, can_manage_event, registration_is_open, seats_left


@login_required
@require_POST
def register(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not registration_is_open(event):
        messages.error(request, "Registration is closed for this event.")
        return redirect("events:detail", pk=event.pk)

    with transaction.atomic():
        registration = Registration.objects.filter(user=request.user, event=event).first()
        if registration and registration.status == Registration.Status.REGISTERED:
            messages.info(request, "You are already registered for this event.")
        elif seats_left(event) == 0:
            messages.error(request, "Sorry, this event is full.")
        else:
            if registration:  # registered before, cancelled, and now registering again
                registration.status = Registration.Status.REGISTERED
                registration.save(update_fields=["status"])
            else:
                Registration.objects.create(user=request.user, event=event)
            messages.success(request, f"You are registered for {event.title}!")

    return redirect("events:detail", pk=event.pk)


@login_required
@require_POST
def cancel_registration(request, event_id):
    registration = get_object_or_404(
        Registration, user=request.user, event_id=event_id, status=Registration.Status.REGISTERED
    )
    if not registration.event.is_upcoming:
        messages.error(request, "You cannot cancel after the event has started.")
    else:
        registration.status = Registration.Status.CANCELLED
        registration.save(update_fields=["status"])
        messages.info(request, "Your registration was cancelled.")
    return redirect("events:detail", pk=event_id)


@login_required
def my_registrations(request):
    now = timezone.now()
    registrations = request.user.registrations.filter(
        status=Registration.Status.REGISTERED
    ).select_related("event", "event__club")
    return render(request, "registrations/my_registrations.html", {
        "upcoming": registrations.filter(event__end_time__gte=now).order_by("event__start_time"),
        "past": registrations.filter(event__end_time__lt=now).order_by("-event__start_time"),
    })


def _event_for_manager(request, event_id):
    event = get_object_or_404(Event.objects.select_related("club"), pk=event_id)
    if not can_manage_event(request.user, event):
        raise PermissionDenied("Only the club's executives and DOSA can see this.")
    return event


@login_required
def event_registrations(request, event_id):
    """Registration and attendance list for one event (executives and DOSA)."""
    event = _event_for_manager(request, event_id)
    registrations = active_registrations(event).select_related("user").order_by("user__first_name")
    return render(request, "registrations/event_registrations.html", {
        "event": event,
        "registrations": registrations,
        "checked_in_count": registrations.filter(checked_in=True).count(),
        "seats_left": seats_left(event),
        "can_manage_checkin": event.club.is_executive(request.user),
    })


# ---------------------------------------------------------------- attendance

def _new_checkin_code():
    # No 0/O or 1/I, so the code is easy to read out loud at the venue
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


@login_required
@require_POST
def generate_checkin_code(request, event_id):
    event = get_object_or_404(Event.objects.select_related("club"), pk=event_id)
    if not event.club.is_executive(request.user):
        raise PermissionDenied("Only the club's executives can create a check-in code.")
    if event.status != Event.Status.APPROVED:
        messages.error(request, "Check-in codes are only for approved events.")
    else:
        event.checkin_code = _new_checkin_code()
        event.save(update_fields=["checkin_code"])
        messages.success(request, f"New check-in code: {event.checkin_code}")
    return redirect("registrations:event_registrations", event_id=event.pk)


@login_required
@require_POST
def checkin(request, event_id):
    """A registered student types the code shown at the venue."""
    event = get_object_or_404(Event, pk=event_id, status=Event.Status.APPROVED)
    registration = Registration.objects.filter(
        user=request.user, event=event, status=Registration.Status.REGISTERED
    ).first()
    code = request.POST.get("code", "").strip().upper()

    if registration is None:
        messages.error(request, "You need to be registered for this event to check in.")
    elif registration.checked_in:
        messages.info(request, "You have already checked in.")
    elif event.has_ended:
        messages.error(request, "This event has already ended.")
    elif not event.checkin_code or code != event.checkin_code:
        messages.error(request, "That check-in code is not correct.")
    else:
        registration.checked_in = True
        registration.checked_in_at = timezone.now()
        registration.save(update_fields=["checked_in", "checked_in_at"])
        messages.success(request, "You are checked in. Enjoy the event!")
    return redirect("events:detail", pk=event.pk)


@login_required
def export_attendance(request, event_id):
    """Download the attendance list as a CSV file (opens in Excel)."""
    event = _event_for_manager(request, event_id)
    date = timezone.localtime(event.start_time).strftime("%Y-%m-%d")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance-{slugify(event.title)}-{date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["Name", "Student ID", "Email", "Registered at", "Checked in", "Checked in at"])
    for r in active_registrations(event).select_related("user").order_by("user__first_name"):
        writer.writerow([
            str(r.user),
            r.user.student_id,
            r.user.email,
            timezone.localtime(r.registered_at).strftime("%Y-%m-%d %H:%M"),
            "Yes" if r.checked_in else "No",
            timezone.localtime(r.checked_in_at).strftime("%Y-%m-%d %H:%M") if r.checked_in_at else "",
        ])
    return response


# ---------------------------------------------------------------- DOSA report

@dosa_required
def participation_report(request):
    """Events, registrations and attendance per club."""
    counted = [Event.Status.APPROVED, Event.Status.COMPLETED]
    clubs = Club.objects.filter(is_active=True).annotate(
        event_count=Count(
            "events", filter=Q(events__status__in=counted), distinct=True
        ),
        registration_count=Count(
            "events__registrations",
            filter=Q(events__status__in=counted,
                     events__registrations__status=Registration.Status.REGISTERED),
            distinct=True,
        ),
        attendance_count=Count(
            "events__registrations",
            filter=Q(events__status__in=counted, events__registrations__checked_in=True),
            distinct=True,
        ),
    ).order_by("-attendance_count", "name")

    totals = {
        key: sum(getattr(club, key) for club in clubs)
        for key in ("event_count", "registration_count", "attendance_count")
    }
    return render(request, "registrations/participation_report.html", {
        "clubs": clubs,
        "totals": totals,
    })
