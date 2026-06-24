import hashlib

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache


def login_attempt_key(request, email):
    remote_address = request.META.get("REMOTE_ADDR", "unknown")
    identity = f"{remote_address}|{(email or '').strip().casefold()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"guios:login-attempts:{digest}"


def is_login_blocked(key):
    return int(cache.get(key, 0)) >= settings.LOGIN_MAX_ATTEMPTS


def register_failed_login(key):
    if cache.add(key, 1, timeout=settings.LOGIN_LOCKOUT_SECONDS):
        return

    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=settings.LOGIN_LOCKOUT_SECONDS)


def clear_failed_logins(key):
    cache.delete(key)


class InitialPasswordTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        last_login = user.last_login
        if last_login is not None:
            last_login = last_login.replace(microsecond=0, tzinfo=None)
        profile_updated_at = user.profile.updated_at.replace(
            microsecond=0,
            tzinfo=None,
        )
        return (
            f"{user.pk}{user.password}{last_login}{timestamp}{user.is_active}"
            f"{user.profile.must_change_password}{profile_updated_at}"
        )


initial_password_token_generator = InitialPasswordTokenGenerator()
