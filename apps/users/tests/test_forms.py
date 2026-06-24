from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.forms import AdminUserCreateForm, EmailAuthenticationForm, generate_username
from apps.users.models import UserRole
from urllib.parse import urlparse


class EmailAuthenticationFormTests(TestCase):
    def test_authenticates_with_email(self):
        User = get_user_model()
        User.objects.create_user(
            username="gabo",
            email="gabo@example.com",
            password="secret-123",
        )

        form = EmailAuthenticationForm(
            request=None,
            data={
                "username": "gabo@example.com",
                "password": "secret-123",
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user().username, "gabo")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AdminUserCreateFormTests(TestCase):
    def test_generate_username_uses_name_and_last_name_without_spaces(self):
        username = generate_username("Gabriel Leonardo", "Hasqui Ortega")

        self.assertEqual(username, "gabriel.hasqui")
        self.assertNotIn(" ", username)

    def test_create_user_assigns_role_and_generated_username(self):
        form = AdminUserCreateForm(
            data={
                "first_name": "Maria",
                "last_name": "Lopez",
                "email": "maria@example.com",
                "role": UserRole.EVALUATOR,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        request_user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        request_user.profile.role = UserRole.ADMIN
        request_user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_login(request_user)
        response = self.client.post(
            reverse("users_admin"),
            data={**form.data, "action": "create-user"},
        )
        user = get_user_model().objects.get(email="maria@example.com")

        self.assertEqual(user.username, "maria.lopez")
        self.assertEqual(user.profile.role, UserRole.EVALUATOR)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.profile.must_change_password)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Definir contrasena", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")
        html_message = mail.outbox[0].alternatives[0][0]
        self.assertIn("GUIOS+", html_message)
        self.assertIn("maria@example.com", html_message)
        self.assertIn("Evaluador", html_message)
        self.assertIn("Definir contraseña", html_message)
        self.assertFalse(user.has_usable_password())

        setup_url = next(
            line.split(": ", 1)[1]
            for line in mail.outbox[0].body.splitlines()
            if line.startswith("Definir contrasena y acceder:")
        )
        setup_path = urlparse(setup_url).path
        setup_response = self.client.get(setup_path)
        self.assertEqual(setup_response.status_code, 200)

        password_response = self.client.post(
            setup_path,
            data={
                "new_password1": "NuevaClaveSegura123!",
                "new_password2": "NuevaClaveSegura123!",
            },
        )
        user.refresh_from_db()
        self.assertRedirects(password_response, reverse("login"))
        self.assertTrue(user.check_password("NuevaClaveSegura123!"))
        self.assertFalse(user.profile.must_change_password)

        reused_response = self.client.get(setup_path)
        self.assertEqual(reused_response.status_code, 400)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class FirstAccessFlowTests(TestCase):
    def test_user_with_pending_password_change_is_redirected(self):
        user = get_user_model().objects.create_user(
            username="usuario.prueba",
            email="usuario@example.com",
            password="Temporal123!",
        )
        user.profile.must_change_password = True
        user.profile.save(update_fields=["must_change_password", "updated_at"])

        self.client.force_login(user)
        response = self.client.get(reverse("profile"))

        self.assertRedirects(response, reverse("force_password_change"))

    def test_force_password_change_clears_flag(self):
        user = get_user_model().objects.create_user(
            username="usuario.prueba",
            email="usuario@example.com",
            password="Temporal123!",
        )
        user.profile.must_change_password = True
        user.profile.save(update_fields=["must_change_password", "updated_at"])

        self.client.force_login(user)
        response = self.client.post(
            reverse("force_password_change"),
            data={
                "new_password1": "NuevaClaveSegura123!",
                "new_password2": "NuevaClaveSegura123!",
            },
        )

        user.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(user.profile.must_change_password)


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        self.admin.profile.role = UserRole.ADMIN
        self.admin.profile.save(update_fields=["role", "updated_at"])
        self.user = get_user_model().objects.create_user(
            username="maria.lopez",
            email="maria@example.com",
            password="Temporal123!",
            first_name="Maria",
            last_name="Lopez",
        )
        self.client.force_login(self.admin)

    def test_admin_can_update_user(self):
        response = self.client.post(
            reverse("users_admin"),
            data={
                "action": "edit-user",
                "user_id": self.user.pk,
                "first_name": "Maria Elena",
                "last_name": "Lopez",
                "email": "maria.elena@example.com",
                "role": UserRole.ADMIN,
                "is_active": "on",
            },
        )

        self.user.refresh_from_db()
        self.assertRedirects(response, reverse("users_admin"))
        self.assertEqual(self.user.first_name, "Maria Elena")
        self.assertEqual(self.user.email, "maria.elena@example.com")
        self.assertEqual(self.user.profile.role, UserRole.ADMIN)
        self.assertFalse(self.user.is_staff)

    def test_edit_button_marks_only_the_current_user(self):
        response = self.client.get(reverse("users_admin"))

        self.assertContains(
            response,
            f'data-edit-user-id="{self.admin.pk}"',
        )
        self.assertContains(response, 'data-edit-is-current-user="true"', count=1)

    def test_admin_can_disable_user_from_edit_form(self):
        response = self.client.post(
            reverse("users_admin"),
            data={
                "action": "edit-user",
                "user_id": self.user.pk,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email,
                "role": UserRole.EVALUATOR,
            },
        )

        self.user.refresh_from_db()
        self.assertRedirects(response, reverse("users_admin"))
        self.assertFalse(self.user.is_active)

    def test_admin_cannot_disable_own_account(self):
        response = self.client.post(
            reverse("users_admin"),
            data={
                "action": "edit-user",
                "user_id": self.admin.pk,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
                "email": self.admin.email,
                "role": UserRole.ADMIN,
            },
        )

        self.admin.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.admin.is_active)
        self.assertContains(response, "No puedes desactivar tu propia cuenta.")

    def test_admin_can_delete_user_without_evaluations(self):
        response = self.client.post(
            reverse("users_admin"),
            data={
                "action": "delete-user",
                "user_id": self.user.pk,
            },
        )

        self.assertRedirects(response, reverse("users_admin"))
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())
