"""Reglas de negocio y seguridad del módulo de Administración."""

from cuentas.models import Usuario


def es_ultimo_superadmin_activo(usuario):
    """Indica si el usuario es el único SuperAdmin activo en el sistema."""
    if not (usuario.pk and usuario.is_active and usuario.rol_id and usuario.rol.es_superadmin):
        return False
    return not Usuario.objects.filter(
        is_active=True,
        rol__es_superadmin=True,
    ).exclude(pk=usuario.pk).exists()
