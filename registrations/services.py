"""Small helper functions about registrations, used by views and templates."""
from events.models import Event

from .models import Registration


def active_registrations(event):
    """Registrations that are not cancelled."""
    return event.registrations.filter(status=Registration.Status.REGISTERED)


def seats_left(event):
    return max(event.capacity - active_registrations(event).count(), 0)


def registration_is_open(event):
    """Students can register only for approved events that have not started."""
    return event.status == Event.Status.APPROVED and event.is_upcoming


def can_manage_event(user, event):
    """Club executives and DOSA can see an event's registration list."""
    return user.is_authenticated and (user.is_dosa or event.club.is_executive(user))
