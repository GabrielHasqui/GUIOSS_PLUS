from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.evaluations.models import Evaluation
from apps.users.models import UserRole


class UserDatabaseIntegrityTests(TestCase):
    def test_email_is_unique_ignoring_case(self):
        User = get_user_model()
        User.objects.create_user(
            username="first.user",
            email="person@example.com",
            password="pass12345",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                username="second.user",
                email="PERSON@example.com",
                password="pass12345",
            )

    def test_profile_rejects_unknown_role_at_database_level(self):
        user = get_user_model().objects.create_user(
            username="role.user",
            email="role@example.com",
            password="pass12345",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            type(user.profile).objects.filter(pk=user.profile.pk).update(role="owner")


class UserDataAuthorizationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass12345",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass12345",
        )
        self.evaluation = Evaluation.objects.create(
            software_name="Private software",
            context="Private context",
            created_by=self.owner,
        )
        self.client.force_login(self.other_user)

    def test_evaluator_cannot_access_another_users_evaluation(self):
        protected_routes = [
            reverse("factors", args=[self.evaluation.pk]),
            reverse("subfactors", args=[self.evaluation.pk]),
            reverse("result", args=[self.evaluation.pk]),
            reverse("history", args=[self.evaluation.pk]),
            reverse("evaluation_report_pdf", args=[self.evaluation.pk]),
        ]

        for route in protected_routes:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 404)

    def test_evaluator_cannot_access_admin_history(self):
        response = self.client.get(reverse("admin_history"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_admin_can_access_another_users_evaluation(self):
        self.other_user.profile.role = UserRole.ADMIN
        self.other_user.profile.save(update_fields=["role", "updated_at"])

        response = self.client.get(reverse("factors", args=[self.evaluation.pk]))

        self.assertEqual(response.status_code, 200)


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username="rate.limited",
            email="rate@example.com",
            password="CorrectPassword123!",
        )

    def test_login_is_temporarily_blocked_after_repeated_failures(self):
        for _ in range(5):
            response = self.client.post(
                reverse("login"),
                data={"username": self.user.email, "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, 200)

        blocked_response = self.client.post(
            reverse("login"),
            data={"username": self.user.email, "password": "wrong-password"},
        )

        self.assertEqual(blocked_response.status_code, 429)

    def test_security_headers_are_present(self):
        response = self.client.get(reverse("login"))

        self.assertIn("Content-Security-Policy", response)
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
