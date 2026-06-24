from .models import UserProfile, UserRole


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": UserRole.ADMIN
            if user.is_staff or user.is_superuser
            else UserRole.EVALUATOR,
        },
    )
    return profile


def is_guios_admin(user):
    if not user.is_authenticated:
        return False

    profile = get_or_create_profile(user)
    return profile.role == UserRole.ADMIN
