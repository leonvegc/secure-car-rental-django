"""
RFD-9.1: Cliente.

DATO SENSIBLE: numero_licencia y datos personales. Reglas:
- Solo roles con "clientes.ver" pueden verlos (el Auditor NO lo tiene).
- En listados la licencia se muestra enmascarada ({{ valor|enmascarar }}).
"""

from django.core.validators import RegexValidator
from django.db import models

from cuentas.validators import validar_identificacion, validar_texto_nombre

validar_licencia = RegexValidator(
    r"^[A-Z0-9-]{5,20}$", "La licencia debe tener de 5 a 20 caracteres: letras mayúsculas, números o guion."
)
validar_telefono = RegexValidator(r"^[0-9]{8}$", "El teléfono debe tener 8 dígitos.")


class Cliente(models.Model):
    cedula = models.CharField(max_length=12, unique=True, validators=[validar_identificacion])
    nombre_completo = models.CharField(max_length=100, validators=[validar_texto_nombre])
    numero_licencia = models.CharField(max_length=20, validators=[validar_licencia])
    vencimiento_licencia = models.DateField("fecha de vencimiento de la licencia")
    telefono = models.CharField(max_length=8, blank=True, validators=[validar_telefono])
    correo = models.EmailField(max_length=254, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre_completo"]

    def save(self, *args, **kwargs):
        if self.numero_licencia:
            self.numero_licencia = self.numero_licencia.strip().upper()
        super().save(*args, **kwargs)

    def licencia_vigente_hasta(self, fecha):
        """True si la licencia sigue vigente en la fecha dada (RN-9.1)."""
        return self.vencimiento_licencia >= fecha

    def __str__(self):
        return f"{self.nombre_completo} ({self.cedula})"
