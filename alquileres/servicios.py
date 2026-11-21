"""
Lógica de negocio del módulo de Alquileres (RFD-9.2 a 9.5, RN-9.1 a 9.3).

Toda la lógica vive aquí y no en las vistas, para poder probarla directamente.
Solo se usa el ORM: nada de SQL crudo.
"""

from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

from vehiculos.models import Vehiculo

from .models import Alquiler


class ReglaNegocioError(Exception):
    """Se rechaza una operación porque incumple una regla de negocio."""


def _activos_traslapados(inicio, fin):
    """
    Alquileres ACTIVO que se traslapan con el rango [inicio, fin).

    Dos rangos [a_ini, a_fin) y [b_ini, b_fin) se traslapan si
    a_ini < b_fin y b_ini < a_fin. Si uno termina el mismo día que el otro
    empieza, NO se traslapan. Es la única definición de traslape del módulo.
    """
    return Alquiler.objects.filter(
        estado=Alquiler.Estado.ACTIVO,
        fecha_inicio__lt=fin,
        fecha_fin__gt=inicio,
    )


def vehiculos_disponibles(inicio, fin):
    """
    RFD-9.4: vehículos que se pueden alquilar en el rango [inicio, fin).

    Un vehículo está disponible si:
    - no está en MANTENIMIENTO (RN-9.2), y
    - no tiene ningún alquiler ACTIVO que se traslape con el rango pedido.

    El estado ALQUILADO no excluye por sí solo: un vehículo alquilado hoy
    puede quedar disponible para un rango futuro que no choque.
    """
    traslapados = _activos_traslapados(inicio, fin).filter(vehiculo=OuterRef("pk"))
    return Vehiculo.objects.exclude(estado=Vehiculo.Estado.MANTENIMIENTO).exclude(Exists(traslapados))


@transaction.atomic
def crear_alquiler(*, cliente, vehiculo, fecha_inicio, fecha_fin, usuario):
    """
    RFD-9.2: asigna un vehículo a un cliente por un rango de fechas.

    Valida en el servidor, en este orden, y lanza ReglaNegocioError:
      1. RN-9.3: el alquiler es de mínimo 1 día (fecha_fin > fecha_inicio).
      2. La fecha de inicio no puede ser anterior a hoy.
      3. RN-9.2: el vehículo no está en mantenimiento.
      4. El vehículo no tiene otro alquiler ACTIVO que se traslape.
      5. RN-9.1: la licencia del cliente está vigente hasta la fecha final.

    Los días, la tarifa y el total se calculan aquí: nunca vienen del usuario.
    """
    if fecha_fin <= fecha_inicio:
        raise ReglaNegocioError("El alquiler debe ser de al menos 1 día.")
    if fecha_inicio < timezone.localdate():
        raise ReglaNegocioError("La fecha de inicio no puede ser anterior a hoy.")

    # Se bloquea la fila del vehículo hasta terminar la transacción: si dos
    # agentes intentan alquilar el mismo carro a la vez, el segundo espera y
    # luego ve el alquiler del primero (evita la condición de carrera).
    vehiculo = Vehiculo.objects.select_for_update().get(pk=vehiculo.pk)

    if vehiculo.estado == Vehiculo.Estado.MANTENIMIENTO:
        raise ReglaNegocioError("El vehículo está en mantenimiento y no se puede alquilar.")
    if _activos_traslapados(fecha_inicio, fecha_fin).filter(vehiculo=vehiculo).exists():
        raise ReglaNegocioError("El vehículo ya está alquilado en esas fechas.")
    if not cliente.licencia_vigente_hasta(fecha_fin):
        raise ReglaNegocioError("La licencia del cliente no estará vigente durante todo el alquiler.")

    dias = (fecha_fin - fecha_inicio).days
    tarifa = vehiculo.tarifa_diaria  # Decimal: se copia al alquiler en este momento
    alquiler = Alquiler.objects.create(
        cliente=cliente,
        vehiculo=vehiculo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias=dias,
        tarifa_diaria=tarifa,
        total=tarifa * dias,
        registrado_por=usuario,
    )
    vehiculo.estado = Vehiculo.Estado.ALQUILADO
    vehiculo.save(update_fields=["estado", "actualizado_en"])
    return alquiler