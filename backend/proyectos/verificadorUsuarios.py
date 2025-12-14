from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.core.exceptions import PermissionDenied

class MyAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        # Evitar que cualquiera se registre
        return True

    def clean_email(self, email):
        email = super().clean_email(email)

        allowed = getattr(settings, "ALLOWED_GOOGLE_EMAILS", [])

        if allowed and email not in allowed:
            raise PermissionDenied("No tienes permiso para usar este correo.")

        return email
