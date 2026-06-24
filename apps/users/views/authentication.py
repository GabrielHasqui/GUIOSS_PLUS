from django.contrib.auth.views import LoginView
from django.conf import settings
from django.urls import reverse
import logging

from ..forms import EmailAuthenticationForm
from ..security import (
    clear_failed_logins,
    is_login_blocked,
    login_attempt_key,
    register_failed_login,
)


security_logger = logging.getLogger("guios.security")


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "registration/login.html"

    def post(self, request, *args, **kwargs):
        self.login_attempt_cache_key = login_attempt_key(
            request,
            request.POST.get("username", ""),
        )

        if is_login_blocked(self.login_attempt_cache_key):
            security_logger.warning(
                "login_rate_limited remote_address=%s",
                request.META.get("REMOTE_ADDR", "unknown"),
            )
            form = self.get_form()
            form.add_error(
                None,
                (
                    "Demasiados intentos de acceso. "
                    f"Intenta nuevamente en {settings.LOGIN_LOCKOUT_SECONDS // 60} minutos."
                ),
            )
            return self.render_to_response(
                self.get_context_data(form=form),
                status=429,
            )

        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        register_failed_login(self.login_attempt_cache_key)
        return super().form_invalid(form)

    def form_valid(self, form):
        clear_failed_logins(self.login_attempt_cache_key)
        return super().form_valid(form)

    def get_success_url(self):
        if hasattr(self.request.user, "profile") and self.request.user.profile.must_change_password:
            return reverse("force_password_change")

        return super().get_success_url()
