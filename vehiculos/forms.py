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
