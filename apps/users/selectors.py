from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from apps.evaluations.models import Evaluation, EvaluationStatus
from apps.evaluations.selectors import get_active_evaluation, get_software_history_data

from .models import UserRole


def get_profile_context_data(user):
    user_evaluations = Evaluation.objects.filter(created_by=user)

    return {
        "active_nav": "profile",
        "evaluation": get_active_evaluation(user),
        "user_evaluations_count": user_evaluations.count(),
        "completed_evaluations_count": user_evaluations.filter(
            status=EvaluationStatus.COMPLETED,
        ).count(),
        "in_progress_evaluations_count": user_evaluations.exclude(
            status=EvaluationStatus.COMPLETED,
        ).count(),
        "software_count": (
            user_evaluations.exclude(software_name="")
            .values("software_name")
            .distinct()
            .count()
        ),
        "active_user_evaluation": (
            user_evaluations.exclude(status=EvaluationStatus.COMPLETED)
            .order_by("-updated_at", "-created_at")
            .first()
        ),
        "latest_user_evaluation": (
            user_evaluations.order_by("-updated_at", "-created_at").first()
        ),
    }


def get_admin_users_queryset():
    return User.objects.select_related("profile").order_by(
        "first_name",
        "last_name",
        "username",
    )


def get_admin_user(user_id):
    return get_object_or_404(User.objects.select_related("profile"), pk=user_id)


def get_admin_base_context_data(user=None):
    return {
        "active_nav": "admin",
        "evaluation": get_active_evaluation(user),
    }


def get_admin_users_context_data():
    return {
        **get_admin_base_context_data(),
        "admin_menu": "users",
        "users": get_admin_users_queryset(),
        "user_roles": UserRole.choices,
    }
def get_admin_history_context_data(user=None):
    return {
        **get_admin_base_context_data(user),
        "admin_menu": "history",
        **get_software_history_data(user),
    }
