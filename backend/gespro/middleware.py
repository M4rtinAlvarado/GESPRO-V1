from django.shortcuts import redirect
from django.urls import reverse

PUBLIC_PATHS = [
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/google/login/',
    '/accounts/microsoft/login/',
    '/accounts/',  # allauth urls
    '/admin/login/',
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Permitir acceso sin login a las rutas públicas
        if any(request.path.startswith(path) for path in PUBLIC_PATHS):
            return self.get_response(request)

        # Si el usuario no está autenticado, enviarlo al login
        if not request.user.is_authenticated:
            return redirect(reverse('account_login'))

        return self.get_response(request)
