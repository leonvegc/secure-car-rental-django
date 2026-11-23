"""Formularios del módulo de Clientes (RFD-9.1)."""

from django import forms

from .models import Cliente


class FiltroClientesForm(forms.Form):
    """Búsqueda por cédula o nombre (GET). Se valida antes de llegar al ORM."""

    q = forms.CharField(label="Cédula o nombre", required=False, max_length=50, strip=True)


class LicenciaField(forms.CharField):
    """Pasa la licencia a mayúsculas ANTES de validarla ('lic-0001' -> 'LIC-0001')."""

    def to_python(self, value):
        return super().to_python(value).upper()


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["cedula", "nombre_completo", "numero_licencia", "vencimiento_licencia", "telefono", "correo"]
        field_classes = {"numero_licencia": LicenciaField}
        widgets = {"vencimiento_licencia": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}
        error_messages = {"cedula": {"unique": "Ya existe un cliente con esa cédula."}}
