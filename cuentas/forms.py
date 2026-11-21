from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        max_length=30,
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Contraseña",
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        # Mensaje genérico: no revela si el usuario existe (anti-enumeración).
        "invalid_login": "Usuario o contraseña incorrectos.",
        "inactive": "Usuario o contraseña incorrectos.",
    }
