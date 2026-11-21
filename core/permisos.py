"""
UTN-05 / UTN-06: control de acceso basado en roles.

Toda vista que lea o modifique datos DEBE usar uno de estos mecanismos:

    @requiere_permiso("vehiculos.crear")            # vistas de función
    class MiVista(PermisoRequeridoMixin, View):     # vistas de clase
        permiso_requerido = "vehiculos.crear"

    @solo_superadmin / SoloSuperAdminMixin           # roles, auditoría

Si el usuario no tiene el permiso se lanza PermissionDenied: Django responde
HTTP 403 con la plantilla errores/403.html y core.views.error_403 lo registra
en la auditoría.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied


def _verificar(request, permisos, todos=True):
    usuario = request.user
    if not usuario.is_authenticated:
        raise PermissionDenied
    if isinstance(permisos, str):
        permisos = (permisos,)
    tiene = [usuario.tiene_permiso(p) for p in permisos]
    if not (all(tiene) if todos else any(tiene)):
        raise PermissionDenied(f"Falta permiso: {', '.join(permisos)}")


def requiere_permiso(*permisos, todos=True):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            _verificar(request, permisos, todos)
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


def solo_superadmin(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.es_superadmin):
            raise PermissionDenied("Solo SuperAdmin")
        return vista(request, *args, **kwargs)

    return envoltura


class PermisoRequeridoMixin:
    """permiso_requerido puede ser un str o una tupla (se exigen todos)."""

    permiso_requerido = None

    def dispatch(self, request, *args, **kwargs):
        if not self.permiso_requerido:
            raise PermissionDenied("Vista sin permiso configurado")  # falla cerrada
        _verificar(request, self.permiso_requerido)
        return super().dispatch(request, *args, **kwargs)


class SoloSuperAdminMixin:
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.es_superadmin):
            raise PermissionDenied("Solo SuperAdmin")
        return super().dispatch(request, *args, **kwargs)
