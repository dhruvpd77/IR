from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and not user.is_active:
            logout(request)
            messages.error(request, 'This account is deactivated. Ask a super admin to turn it back on.')
            return redirect('login')
        return self.get_response(request)
