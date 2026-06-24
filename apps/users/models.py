from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Administrador"
    EVALUATOR = "evaluator", "Evaluador"


class UserProfile(models.Model):
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EVALUATOR,
    )
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"
        constraints = [
            models.CheckConstraint(condition=models.Q(role__in=UserRole.values), name="users_profile_role_valid"),
        ]

    def __str__(self):
        return f"{self.user.username} - {UserRole(self.role).label}"
