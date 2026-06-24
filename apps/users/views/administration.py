from django.contrib import messages
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..permissions import is_guios_admin
from ..selectors import (
    get_admin_history_context_data,
    get_admin_user,
    get_admin_users_context_data,
)
from ..services import (
    build_admin_user_form,
    build_admin_user_update_form,
    create_admin_user_from_form,
    delete_admin_user,
    resend_initial_access_email,
    update_admin_user_from_form,
)


security_logger = logging.getLogger("guios.security")


@login_required
def users_admin(request):
    if not is_guios_admin(request.user):
        messages.warning(request, "No tienes permisos para acceder a administracion.")
        return redirect("dashboard")

    action = request.POST.get("action") if request.method == "POST" else None
    form, open_create_modal = build_admin_user_form(
        request.POST if action == "create-user" else None
    )
    edit_form = None
    editing_user = None
    open_edit_modal = False

    if action == "create-user":
        user = create_admin_user_from_form(request, form)

        if user is not None:
            security_logger.info(
                "admin_user_created actor_id=%s target_id=%s role=%s",
                request.user.pk,
                user.pk,
                user.profile.role,
            )
            messages.success(
                request,
                (
                    f"Usuario {user.get_full_name() or user.username} creado correctamente. "
                    f"Se envio un enlace seguro de acceso al correo {user.email}."
                ),
            )
            return redirect("users_admin")
    elif action == "edit-user":
        editing_user = get_admin_user(request.POST.get("user_id"))
        edit_form = build_admin_user_update_form(
            editing_user,
            request.user,
            request.POST,
        )
        open_edit_modal = True
        updated_user = update_admin_user_from_form(edit_form)

        if updated_user is not None:
            security_logger.info(
                "admin_user_updated actor_id=%s target_id=%s role=%s active=%s",
                request.user.pk,
                updated_user.pk,
                updated_user.profile.role,
                updated_user.is_active,
            )
            messages.success(
                request,
                f"Usuario {updated_user.get_full_name() or updated_user.username} actualizado correctamente.",
            )
            return redirect("users_admin")
    elif action == "delete-user":
        target_user = get_admin_user(request.POST.get("user_id"))
        target_user_id = target_user.pk
        success, message = delete_admin_user(target_user, request.user)
        if success:
            security_logger.info(
                "admin_user_deleted actor_id=%s target_id=%s",
                request.user.pk,
                target_user_id,
            )
            messages.success(request, message)
        else:
            messages.warning(request, message)
        return redirect("users_admin")
    elif action == "resend-access":
        target_user = get_admin_user(request.POST.get("user_id"))
        try:
            success, message = resend_initial_access_email(request, target_user)
        except Exception:
            success = False
            message = "No fue posible enviar el enlace de acceso. Intenta nuevamente."

        if success:
            security_logger.info(
                "initial_access_resent actor_id=%s target_id=%s",
                request.user.pk,
                target_user.pk,
            )
            messages.success(request, message)
        else:
            messages.warning(request, message)
        return redirect("users_admin")

    context = {
        **get_admin_users_context_data(),
        "form": form,
        "open_create_modal": open_create_modal,
        "edit_form": edit_form,
        "editing_user": editing_user,
        "open_edit_modal": open_edit_modal,
    }
    return render(request, "users/admin_users.html", context)


@login_required
def admin_history(request):
    if not is_guios_admin(request.user):
        messages.warning(request, "No tienes permisos para acceder a administracion.")
        return redirect("dashboard")

    return render(
        request,
        "users/admin_history.html",
        get_admin_history_context_data(request.user),
    )
