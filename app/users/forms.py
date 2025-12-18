from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django import forms
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = None

    class Meta:
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    username = None

    class Meta:
        model = User
        fields = ("email",)


class CustomAuthenticationForm(AuthenticationForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={"autofocus": True}))


class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña Antigua"}),
        label="InputContraseñaOld",
        required=True,
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Nueva Contraseña"}),
        label="Nueva Contraseña",
        required=True,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmar Nueva Contraseña"}),
        label="Confirmar Nueva Contraseña",
        required=True,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise ValidationError("La contraseña antigua no es válida.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        # Ensure both fields are present
        if not new_password:
            raise ValidationError("El campo de nueva contraseña es obligatorio.")
        if not confirm_password:
            raise ValidationError("El campo de confirmación de contraseña es obligatorio.")

        # Check if the new passwords match
        if new_password != confirm_password:
            raise ValidationError("Las contraseñas nuevas no coinciden.")

        # Validate the new password using Django's built-in validators
        try:
            validate_password(new_password, self.user)
        except ValidationError as e:
            self.add_error("new_password", e)

        return cleaned_data
