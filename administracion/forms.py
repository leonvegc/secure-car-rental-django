"""Formularios del módulo de Administración (UTN-04, UTN-05, UTN-06, UTN-09)."""

from django import forms
from django.contrib.auth.password_validation import validate_password

from cuentas.models import Usuario

from .servicios import es_ultimo_superadmin_activo


class EmailMinusculaField(forms.EmailField):
    """Normaliza el correo a minúsculas y sin espacios antes de validar unicidad."""

    def to_python(self, value):
        valor = super().to_python(value)
        return valor.strip().lower() if valor else valor


class FiltroUsuariosForm(forms.Form):
    """Filtro de búsqueda para la lista de usuarios (GET)."""

    q = forms.CharField(
        label="Buscar por usuario o nombre",
        required=False,
        max_length=50,
        strip=True,
    )


class _UsuarioBaseForm(forms.ModelForm):
    """Campos y saneamiento compartidos al crear y editar usuarios."""

    class Meta:
        model = Usuario
        fields = ["username", "nombre_completo", "identificacion", "email", "rol", "is_active"]
        field_classes = {"email": EmailMinusculaField}
        error_messages = {
            "username": {"unique": "Ya existe un usuario con ese nombre de usuario."},
            "identificacion": {"unique": "Ya existe un usuario con esa identificación."},
            "email": {"unique": "Ya existe un usuario con ese correo."},
        }

    def clean_username(self):
        return self.cleaned_data["username"].strip()

    def clean_nombre_completo(self):
        return self.cleaned_data["nombre_completo"].strip()

    def clean_identificacion(self):
        return self.cleaned_data["identificacion"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class UsuarioCrearForm(_UsuarioBaseForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mínimo 12 caracteres, con mayúscula, minúscula, número y símbolo.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        datos = super().clean()
        p1 = datos.get("password1")
        p2 = datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        elif p1:
            usuario_temporal = Usuario(
                username=datos.get("username", ""),
                nombre_completo=datos.get("nombre_completo", ""),
                email=datos.get("email", ""),
            )
            try:
                validate_password(p1, usuario_temporal)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(_UsuarioBaseForm):
    nueva_password1 = forms.CharField(
        label="Nueva contraseña (opcional)",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Déjelo vacío para conservar la contraseña actual.",
    )
    nueva_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self._rol_original_id = self.instance.rol_id
        self._era_ultimo_superadmin = es_ultimo_superadmin_activo(self.instance)

    def clean_rol(self):
        rol = self.cleaned_data["rol"]
        if self.actor and self.instance.pk == self.actor.pk and rol.pk != self._rol_original_id:
            raise forms.ValidationError("No puede cambiar su propio rol.")
        if self._era_ultimo_superadmin and not rol.es_superadmin:
            raise forms.ValidationError(
                "No puede cambiar el rol del último SuperAdmin activo del sistema."
            )
        return rol

    def clean_is_active(self):
        activo = self.cleaned_data["is_active"]
        if self.actor and self.instance.pk == self.actor.pk and not activo:
            raise forms.ValidationError("No puede desactivar su propia cuenta.")
        if self._era_ultimo_superadmin and not activo:
            raise forms.ValidationError(
                "No puede desactivar al último SuperAdmin activo del sistema."
            )
        return activo

    def clean(self):
        datos = super().clean()
        p1 = datos.get("nueva_password1") or ""
        p2 = datos.get("nueva_password2") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error("nueva_password2", "Las contraseñas no coinciden.")
            else:
                try:
                    validate_password(p1, self.instance)
                except forms.ValidationError as exc:
                    self.add_error("nueva_password1", exc)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva = self.cleaned_data.get("nueva_password1")
        if nueva:
            usuario.set_password(nueva)
        if commit:
            usuario.save()
        return usuario
