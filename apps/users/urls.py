from django.urls import path

from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("first-access/password/", views.force_password_change, name="force_password_change"),
    path(
        "first-access/<uidb64>/<token>/",
        views.initial_password_setup,
        name="initial_password_setup",
    ),
    path("admin/users/", views.users_admin, name="users_admin"),
    path("admin/history/", views.admin_history, name="admin_history"),
]
