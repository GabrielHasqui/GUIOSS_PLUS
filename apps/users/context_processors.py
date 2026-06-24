def short_display_name(user):
    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()

    if first_name and last_name:
        return f"{first_name.split()[0]} {last_name.split()[0]}"

    full_name = (user.get_full_name() or "").strip()
    if full_name:
        return " ".join(full_name.split()[:2])

    return getattr(user, "email", "") or getattr(user, "username", "")


def full_display_name(user):
    full_name = (user.get_full_name() or "").strip()
    return full_name or getattr(user, "email", "") or getattr(user, "username", "")


def user_display(request):
    if request.user.is_authenticated:
        return {
            "header_user_display_name": short_display_name(request.user),
            "menu_user_display_name": full_display_name(request.user),
        }

    return {
        "header_user_display_name": "",
        "menu_user_display_name": "",
    }
