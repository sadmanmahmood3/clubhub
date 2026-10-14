from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def dosa_required(view_func):
    """Only lets DOSA admins open a page. Use it like:

        @dosa_required
        def approval_queue(request): ...
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_dosa:
            raise PermissionDenied("Only DOSA admins can open this page.")
        return view_func(request, *args, **kwargs)

    return wrapper
