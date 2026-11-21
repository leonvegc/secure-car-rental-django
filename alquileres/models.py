"""
RFD-9.2 a 9.5: Alquiler de un vehículo por un rango de fechas.

Reglas de negocio (se validan en alquileres/servicios.py, y las básicas
también con restricciones en la base de datos):
- RN-9.1 No se alquila a un cliente con licencia vencida.
- RN-9.2 No se alquila un vehículo en mantenimiento.
- RN-9.3 El alquiler es de mínimo 1 día (fecha_fin > fecha_inicio).
"""

import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from clientes.models import Cliente
from vehiculos.models import Vehiculo


def generar_codigo():
    return "ALQ-" + secrets.token_hex(4).upper()


class Alquiler(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        FINALIZADO = "FINALIZADO", "Finalizado"

    codigo = models.CharField(max_length=12, unique=True, default=generar_codigo, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="alquileres")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="alquileres")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveIntegerField(validators=[MinValueValidator(1)], editable=False)
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # copia al crear
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO, editable=False)
    fecha_devolucion = models.DateTimeField(null=True, blank=True, editable=False)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+", editable=False
    )
    recibido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_inicio", "-creado_en"]
        verbose_name_plural = "alquileres"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gt=models.F("fecha_inicio")), name="alquiler_minimo_un_dia"
            ),
            models.CheckConstraint(condition=models.Q(dias__gte=1), name="alquiler_dias_positivos"),
            models.CheckConstraint(condition=models.Q(total__gt=0), name="alquiler_total_positivo"),
        ]
        indexes = [models.Index(fields=["vehiculo", "estado", "fecha_inicio", "fecha_fin"])]

    def __str__(self):
        return f"{self.codigo} - {self.vehiculo.placa}"
