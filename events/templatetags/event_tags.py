from django import template
from django.utils import timezone

from events.models import Event

register = template.Library()

STATUS_COLORS = {
    Event.Status.DRAFT: "secondary",
    Event.Status.PENDING: "warning",
    Event.Status.APPROVED: "success",
    Event.Status.REJECTED: "danger",
    Event.Status.COMPLETED: "dark",
}


@register.filter
def status_color(status):
    """{{ event.status|status_color }} -> a Bootstrap colour name for the badge."""
    return STATUS_COLORS.get(status, "secondary")


@register.inclusion_tag("events/_upcoming_events.html")
def club_upcoming_events(club, limit=5):
    """{% club_upcoming_events club %} -> list of the club's next approved events."""
    events = club.events.filter(
        status=Event.Status.APPROVED, end_time__gte=timezone.now()
    )[:limit]
    return {"events": events}
