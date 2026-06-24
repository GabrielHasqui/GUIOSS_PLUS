from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from .forms import AdminUserCreateForm, AdminUserUpdateForm
from .security import initial_password_token_generator


def send_user_welcome_email(user, password_setup_url):
    subject = "Acceso inicial a GUIOS+"
    recipient_name = user.get_full_name() or user.username
    role_name = user.profile.get_role_display()
    message = (
        f"Hola {recipient_name},\n\n"
        "Se ha creado una cuenta para ti en la plataforma GUIOS+, el sistema "
        "de evaluacion de software FLOSS basado en el metodo GUIOSPRO.\n\n"
        f"Usuario: {user.email}\n"
        f"Rol asignado: {role_name}\n\n"
        f"Definir contrasena y acceder: {password_setup_url}\n\n"
        "Este enlace es personal, de un solo uso y expira en 72 horas.\n"
    )
    html_message = render_to_string(
        "users/emails/welcome.html",
        {
            "recipient_name": recipient_name,
            "email": user.email,
            "role_name": role_name,
            "password_setup_url": password_setup_url,
        },
    )

    email_message = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    sent_count = email_message.send(fail_silently=False)

    if sent_count != 1:
        raise RuntimeError("No fue posible enviar el correo de acceso al nuevo usuario.")


def build_password_setup_url(request, user):
    return request.build_absolute_uri(
        reverse(
            "initial_password_setup",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": initial_password_token_generator.make_token(user),
            },
        )
    )


def save_profile_form(form):
    if form.is_valid():
        form.save()
        return True

    return False


def save_password_form(request, password_form):
    if password_form.is_valid():
        updated_user = password_form.save()
        update_session_auth_hash(request, updated_user)
        return True

    return False


def build_admin_user_form(post_data=None):
    if post_data is None:
        return AdminUserCreateForm(), False

    return AdminUserCreateForm(post_data), True


def build_admin_user_update_form(target_user, actor, post_data=None):
    if post_data is None:
        return AdminUserUpdateForm(instance=target_user, actor=actor)

    return AdminUserUpdateForm(post_data, instance=target_user, actor=actor)


def save_first_access_password_form(request, password_form):
    if password_form.is_valid():
        updated_user = password_form.save()
        updated_user.profile.must_change_password = False
        updated_user.profile.save(update_fields=["must_change_password", "updated_at"])
        update_session_auth_hash(request, updated_user)
        return True

    return False


def create_admin_user_from_form(request, form):
    if form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(password=None)
                password_setup_url = build_password_setup_url(request, user)
                send_user_welcome_email(user, password_setup_url)
        except Exception:
            form.add_error(
                None,
                "No fue posible enviar el correo de acceso. Verifica la configuracion del correo e intenta nuevamente.",
            )
            return None

        return user

    return None


def resend_initial_access_email(request, user):
    if not user.profile.must_change_password:
        return False, "El usuario ya configuro su contrasena."

    with transaction.atomic():
        user.profile.updated_at = timezone.now()
        user.profile.save(update_fields=["updated_at"])
        send_user_welcome_email(user, build_password_setup_url(request, user))
    return True, f"Se envio un nuevo enlace de acceso al correo {user.email}."


def update_admin_user_from_form(form):
    if form.is_valid():
        return form.save()

    return None


def delete_admin_user(target_user, actor):
    if target_user.pk == actor.pk:
        return False, "No puedes eliminar tu propia cuenta."

    if target_user.evaluations.exists():
        return (
            False,
            "No se puede eliminar este usuario porque tiene evaluaciones asociadas. Puedes desactivarlo en su lugar.",
        )

    target_user.delete()
    return True, "Usuario eliminado correctamente."
