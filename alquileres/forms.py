"""
Formularios del módulo de Alquileres.

Se usan forms.Form (no ModelForm): así solo existen los campos que declaramos
aquí y nadie puede mandar total, días, estado u otros campos del modelo
(asignación masiva). Los GET de búsqueda también se validan con un formulario.
"""

from django import forms

from clientes.models import Cliente
from vehiculos.models import Vehiculo

from .models import Alquiler


class FiltroAlquileresForm(forms.Form):
    """Filtros de la lista (GET). Se validan antes de usarlos en el ORM."""

    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[("", "Todos")] + Alquiler.Estado.choices,
    )
    q = forms.CharField(label="Código o placa", required=False, max_length=20, strip=True)


class CrearAlquilerForm(forms.Form):
    """RFD-9.2. Solo datos de entrada: días, tarifa y total los calcula el servidor."""

    cliente = forms.ModelChoiceField(label="Cliente", queryset=Cliente.objects.all())
    vehiculo = forms.ModelChoiceField(
        label="Vehículo",
        queryset=Vehiculo.objects.exclude(estado=Vehiculo.Estado.MANTENIMIENTO),
    )
    fecha_inicio = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )


class DisponibilidadForm(forms.Form):
    """RFD-9.4. Consulta GET: el rango se valida antes de tocar la base de datos."""

    RANGO_MAXIMO_DIAS = 366

    inicio = forms.DateField(
        label="Desde",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    fin = forms.DateField(
        label="Hasta",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get("inicio"), datos.get("fin")
        if inicio and fin:
            if fin <= inicio:
                raise forms.ValidationError("La fecha final debe ser posterior a la fecha inicial.")
            if (fin - inicio).days > self.RANGO_MAXIMO_DIAS:
                raise forms.ValidationError(f"El rango máximo de consulta es de {self.RANGO_MAXIMO_DIAS} días.")
        return datos