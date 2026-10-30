from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def roles_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return render(request, 'errors/403.html', status=403)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
