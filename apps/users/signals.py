from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile, UserRole


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    role = UserRole.ADMIN if instance.is_superuser else UserRole.EVALUATOR
    profile, profile_created = UserProfile.objects.get_or_create(
        user=instance,
        defaults={"role": role},
    )

    if profile_created:
        return

    if instance.is_superuser and profile.role != UserRole.ADMIN:
        profile.role = role
        profile.save(update_fields=["role", "updated_at"])
