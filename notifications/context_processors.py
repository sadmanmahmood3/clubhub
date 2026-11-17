def unread_notifications(request):
    """Makes {{ unread_notification_count }} available in every template (for the bell)."""
    if request.user.is_authenticated:
        return {"unread_notification_count": request.user.notifications.filter(is_read=False).count()}
    return {}
