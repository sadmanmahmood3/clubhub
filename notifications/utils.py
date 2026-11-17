from .models import Notification


def notify(users, message, link=""):
    """Send an in-app notification to one user or to a list of users.

        notify(student, "Your request was approved", "/clubs/iub-computer-club/")
        notify([exec1, exec2], "New join request")
    """
    if users is None:
        return
    if hasattr(users, "pk"):  # a single user
        users = [users]
    Notification.objects.bulk_create(
        [Notification(user=user, message=message, link=link) for user in users]
    )
