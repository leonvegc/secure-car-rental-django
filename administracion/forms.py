"""Formularios del módulo de Administración (UTN-04, UTN-05, UTN-06, UTN-09)."""

from django import forms


class FiltroUsuariosForm(forms.Form):
    """Filtro de búsqueda para la lista de usuarios (GET)."""

    q = forms.CharField(
        label="Buscar por usuario o nombre",
        required=False,
        max_length=50,
        strip=True,
    )
