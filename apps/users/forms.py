import re
import unicodedata

from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms

from .models import UserProfile, UserRole


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electronico",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": (
            "Ingresa un correo electronico y contrasena validos. "
            "Ten en cuenta que ambos campos distinguen entre mayusculas y minusculas."
        ),
        "email_not_unique": (
            "Hay mas de un usuario con este correo electronico. "
            "Contacta al administrador."
        ),
    }

    def clean(self):
        email = self.cleaned_data.get("username")

        if email:
            UserModel = get_user_model()
            users = UserModel._default_manager.filter(email__iexact=email)

            if users.count() > 1:
                raise ValidationError(
                    self.error_messages["email_not_unique"],
                    code="email_not_unique",
                )

            user = users.first()

            if user:
                self.cleaned_data["username"] = user.get_username()

        return super().clean()


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre",
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        label="Apellido",
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "family-name",
            }
        ),
    )
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]


def normalize_username_part(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "", value).lower()
    return value or "usuario"


def generate_username(first_name, last_name):
    UserModel = get_user_model()
    first_name_part = (first_name or "").strip().split()[0] if (first_name or "").strip() else ""
    last_name_part = (last_name or "").strip().split()[0] if (last_name or "").strip() else ""
    base = f"{normalize_username_part(first_name_part)}.{normalize_username_part(last_name_part)}"
    username = base
    counter = 2

    while UserModel._default_manager.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    return username


class AdminUserCreateForm(forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Correo electronico")
    role = forms.ChoiceField(label="Rol", choices=UserRole.choices)

    def clean_email(self):
        email = self.cleaned_data["email"]
        UserModel = get_user_model()

        if UserModel._default_manager.filter(email__iexact=email).exists():
            raise ValidationError(
                "Este correo electronico ya esta registrado.",
                code="duplicate_email",
            )

        return email

    def clean(self):
        return super().clean()

    def save(self, password=None):
        UserModel = get_user_model()
        role = self.cleaned_data["role"]
        user = UserModel.objects.create_user(
            username=generate_username(
                self.cleaned_data["first_name"],
                self.cleaned_data["last_name"],
            ),
            email=self.cleaned_data["email"],
            password=password,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            is_staff=False,
            is_superuser=False,
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": role,
                "must_change_password": True,  # nosec B105
            },
        )
        return user


class AdminUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="Correo electronico")
    role = forms.ChoiceField(label="Rol", choices=UserRole.choices)
    is_active = forms.BooleanField(label="Usuario activo", required=False)

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "Nombre"
        self.fields["last_name"].label = "Apellido"
        self.fields["role"].initial = getattr(self.instance.profile, "role", UserRole.EVALUATOR)
        self.fields["is_active"].initial = self.instance.is_active

    def clean_role(self):
        role = self.cleaned_data["role"]

        if self.actor and self.instance.pk == self.actor.pk and role != self.instance.profile.role:
            raise ValidationError(
                "No puedes cambiar tu propio rol desde esta pantalla.",
                code="self_role_change_not_allowed",
            )

        return role

    def clean_is_active(self):
        is_active = self.cleaned_data["is_active"]

        if self.actor and self.instance.pk == self.actor.pk and not is_active:
            raise ValidationError(
                "No puedes desactivar tu propia cuenta.",
                code="self_deactivation_not_allowed",
            )

        return is_active

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data["role"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]

        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role},
            )

        return user


class FirstAccessPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nueva contrasena",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contrasena",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
