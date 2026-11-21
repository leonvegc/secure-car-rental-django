"""
UTN-09: Registro de auditoría (solo escritura, no se edita ni se borra).
"""

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    class Tipo(models.TextChoices):
        LOGIN_OK = "LOGIN_OK", "Inicio de sesión exitoso"
        LOGIN_FALLIDO = "LOGIN_FALLIDO", "Inicio de sesión fallido"
        BLOQUEO = "BLOQUEO", "Cuenta bloqueada por intentos fallidos"
        LOGOUT = "LOGOUT", "Cierre de sesión"
        SESION_EXPIRADA = "SESION_EXPIRADA", "Sesión expirada por inactividad"
        ACCESO_DENEGADO = "ACCESO_DENEGADO", "Acceso denegado (403)"
        CSRF_RECHAZADO = "CSRF_RECHAZADO", "Solicitud rechazada por CSRF (403)"
        CAMBIO_ROL = "CAMBIO_ROL", "Cambio de rol de un usuario"
        CAMBIO_PERMISOS = "CAMBIO_PERMISOS", "Cambio de permisos de un rol"
        GESTION_ROL = "GESTION_ROL", "Creación/edición/borrado de rol"
        GESTION_USUARIO = "GESTION_USUARIO", "Creación/edición/borrado de usuario"
        OPERACION = "OPERACION", "Operación de negocio"

    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registros_auditoria",
    )
    # Copia del username: se conserva aunque el usuario se borre, y guarda
    # el nombre intentado en logins fallidos.
    username = models.CharField(max_length=150, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ruta = models.CharField(max_length=500, blank=True)
    metodo = models.CharField(max_length=10, blank=True)
    detalle = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("Los registros de auditoría no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Los registros de auditoría no se pueden borrar.")

    def __str__(self):
        return f"{self.fecha_hora:%Y-%m-%d %H:%M:%S} {self.tipo} {self.username}"
