"""
Lógica de negocio del módulo de Alquileres (RFD-9.2 a 9.5, RN-9.1 a 9.3).

Toda la lógica vive aquí y no en las vistas, para poder probarla directamente.
Solo se usa el ORM: nada de SQL crudo.
"""

from django.db.models import Exists, OuterRef

from vehiculos.models import Vehiculo

from .models import Alquiler


class ReglaNegocioError(Exception):
    """Se rechaza una operación porque incumple una regla de negocio."""


def vehiculos_disponibles(inicio, fin):
    """
    RFD-9.4: vehículos que se pueden alquilar en el rango [inicio, fin).

    Un vehículo está disponible si:
    - no está en MANTENIMIENTO (RN-9.2), y
    - no tiene ningún alquiler ACTIVO cuyo rango se traslape con el pedido.

    Dos rangos [a_ini, a_fin) y [b_ini, b_fin) se traslapan si
    a_ini < b_fin y b_ini < a_fin. Si uno termina el mismo día que el otro
    empieza, NO se traslapan.

    El estado ALQUILADO no excluye por sí solo: un vehículo alquilado hoy
    puede quedar disponible para un rango futuro que no choque.
    """
    traslapados = Alquiler.objects.filter(
        vehiculo=OuterRef("pk"),
        estado=Alquiler.Estado.ACTIVO,
        fecha_inicio__lt=fin,
        fecha_fin__gt=inicio,
    )
    return Vehiculo.objects.exclude(estado=Vehiculo.Estado.MANTENIMIENTO).exclude(Exists(traslapados))