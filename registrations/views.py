from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
    registrations = request.user.registrations.filter(
        status=Registration.Status.REGISTERED
    ).select_related("event", "event__club").order_by("event__start_time")
    return render(request, "registrations/my_registrations.html", {"registrations": registrations})


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
    })
