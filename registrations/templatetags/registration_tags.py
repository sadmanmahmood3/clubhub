from django import template

from registrations.models import Registration
from registrations.services import registration_is_open, seats_left

register = template.Library()


@register.inclusion_tag("registrations/_registration_box.html", takes_context=True)
def registration_box(context, event):
    """{% registration_box event %} -> the Register / Cancel box on the event page."""
    request = context["request"]
    registration = None
    if request.user.is_authenticated:
        registration = event.registrations.filter(
            user=request.user, status=Registration.Status.REGISTERED
        ).first()
    return {
        "event": event,
        "user": request.user,
        "request": request,
        "registration": registration,
        "seats_left": seats_left(event),
        "is_open": registration_is_open(event),
        "csrf_token": context.get("csrf_token"),
    }
