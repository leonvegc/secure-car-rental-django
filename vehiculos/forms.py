"""Formularios del módulo de Vehículos."""

from django import forms

from .models import Vehiculo


class FiltroVehiculosForm(forms.Form):
    """Filtros de la lista (GET). Se validan antes de llegar al ORM."""

    q = forms.CharField(label="Placa, marca o modelo", required=False, max_length=30, strip=True)
    categoria = forms.ChoiceField(
        label="Categoría", required=False, choices=[("", "Todas")] + Vehiculo.Categoria.choices
    )
    estado = forms.ChoiceField(label="Estado", required=False, choices=[("", "Todos")] + Vehiculo.Estado.choices)


class PlacaField(forms.CharField):
    """Pasa la placa a mayúsculas ANTES de validarla: 'abc-123' se acepta como 'ABC-123'."""

    def to_python(self, value):
        return super().to_python(value).upper()


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ["placa", "marca", "modelo", "categoria", "tarifa_diaria", "estado"]  # lista explícita
        field_classes = {"placa": PlacaField}
        error_messages = {"placa": {"unique": "Ya existe un vehículo con esa placa."}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Un vehículo ALQUILADO solo cambia de estado al devolverlo (módulo de alquileres).
        if self.instance.pk and self.instance.estado == Vehiculo.Estado.ALQUILADO:
            self.fields["estado"].disabled = True
            self.fields["estado"].help_text = "Se actualiza al registrar la devolución."

    def clean_estado(self):
        estado = self.cleaned_data["estado"]
        if self.fields["estado"].disabled:
            return estado  # conserva el valor guardado
        if estado == Vehiculo.Estado.ALQUILADO:
            raise forms.ValidationError("El estado Alquilado lo asigna el módulo de alquileres.")
        if estado == Vehiculo.Estado.MANTENIMIENTO and self.instance.pk:
            if self.instance.alquileres.filter(estado="ACTIVO").exists():
                raise forms.ValidationError("El vehículo tiene un alquiler activo.")
        return estado
