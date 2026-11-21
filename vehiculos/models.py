"""Entidad principal del dominio 9 (UTN-03): Vehículo."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

validar_placa = RegexValidator(
    r"^[A-Z0-9-]{3,10}$",
    "La placa debe tener de 3 a 10 caracteres: letras mayúsculas, números o guion.",
)
validar_texto_corto = RegexValidator(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]{1,50}$",
    "Solo letras, números, espacios, punto y guion.",
)


class Vehiculo(models.Model):
    class Categoria(models.TextChoices):
        ECONOMICO = "ECONOMICO", "Económico"
        SEDAN = "SEDAN", "Sedán"
        SUV = "SUV", "SUV"
        PICKUP = "PICKUP", "Pickup"
        MICROBUS = "MICROBUS", "Microbús"

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        ALQUILADO = "ALQUILADO", "Alquilado"
        MANTENIMIENTO = "MANTENIMIENTO", "Mantenimiento"

    placa = models.CharField(max_length=10, unique=True, validators=[validar_placa])
    marca = models.CharField(max_length=50, validators=[validar_texto_corto])
    modelo = models.CharField(max_length=50, validators=[validar_texto_corto])
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    tarifa_diaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("9999999.99"))],
        help_text="Colones por día",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["placa"]
        constraints = [
            models.CheckConstraint(condition=models.Q(tarifa_diaria__gt=0), name="vehiculo_tarifa_positiva"),
        ]

    def save(self, *args, **kwargs):
        if self.placa:
            self.placa = self.placa.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"
