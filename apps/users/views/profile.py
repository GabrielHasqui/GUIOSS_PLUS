from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from ..forms import FirstAccessPasswordForm, UserProfileForm
from ..selectors import get_profile_context_data
from ..services import (
    save_first_access_password_form,
    save_password_form,
    save_profile_form,
)
from ..security import initial_password_token_generator


@login_required
def profile(request):
    form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    open_profile_modal = False
    open_password_modal = False

    if request.method == "POST" and request.POST.get("action") == "profile":
        form = UserProfileForm(request.POST, instance=request.user)
        open_profile_modal = True

        if save_profile_form(form):
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("profile")

    elif request.method == "POST" and request.POST.get("action") == "password":
        password_form = PasswordChangeForm(request.user, request.POST)
        open_password_modal = True

        if save_password_form(request, password_form):
            messages.success(request, "Contrasena actualizada correctamente.")
            return redirect("profile")

    context = {
        **get_profile_context_data(request.user),
        "form": form,
        "password_form": password_form,
        "open_profile_modal": open_profile_modal,
        "open_password_modal": open_password_modal,
    }
    return render(request, "users/profile.html", context)


@login_required
def force_password_change(request):
    password_form = FirstAccessPasswordForm(request.user)

    if request.method == "POST":
        password_form = FirstAccessPasswordForm(request.user, request.POST)

        if save_first_access_password_form(request, password_form):
            messages.success(
                request,
                "Contrasena actualizada correctamente. Ya puedes usar GUIOS+.",
            )
            return redirect("dashboard")

    return render(
        request,
        "users/force_password_change.html",
        {"password_form": password_form},
    )


def initial_password_setup(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    token_is_valid = bool(
        user
        and user.profile.must_change_password
        and initial_password_token_generator.check_token(user, token)
    )

    if not token_is_valid:
        return render(
            request,
            "users/initial_password_setup_invalid.html",
            status=400,
        )

    password_form = FirstAccessPasswordForm(user)

    if request.method == "POST":
        password_form = FirstAccessPasswordForm(user, request.POST)

        if password_form.is_valid():
            updated_user = password_form.save()
            updated_user.profile.must_change_password = False
            updated_user.profile.save(
                update_fields=["must_change_password", "updated_at"]
            )
            messages.success(
                request,
                "Contrasena configurada correctamente. Ya puedes iniciar sesion.",
            )
            return redirect("login")

    return render(
        request,
        "users/force_password_change.html",
        {
            "password_form": password_form,
            "initial_setup": True,
        },
    )
