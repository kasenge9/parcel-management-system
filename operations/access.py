from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def role_required(*group_names):
    if not group_names:
        raise ValueError("role_required requires at least one group name.")
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Your account is not permitted to perform this action.")
        return wrapped
    return decorator
