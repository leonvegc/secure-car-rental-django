"""
Función única para escribir en el registro de auditoría (UTN-09).

Uso:
    from core.auditoria import registrar_evento
    from core.models import RegistroAuditoria
    registrar_evento(request, RegistroAuditoria.Tipo.CAMBIO_ROL,
                     detalle=f"Usuario {u.username}: rol {anterior} -> {nuevo}")
"""

import logging

from .models import RegistroAuditoria
from .utils import obtener_ip

logger = logging.getLogger("django.security")


def registrar_evento(request, tipo, detalle="", usuario=None, username=None):
    try:
        if usuario is None and request is not None:
            u = getattr(request, "user", None)
            if u is not None and u.is_authenticated:
                usuario = u
        if username is None:
            username = usuario.get_username() if usuario is not None else ""
        RegistroAuditoria.objects.create(
            tipo=tipo,
            usuario=usuario,
            username=str(username)[:150],
            ip=obtener_ip(request) if request is not None else None,
            ruta=(request.path[:500] if request is not None else ""),
            metodo=(request.method[:10] if request is not None else ""),
            detalle=str(detalle)[:2000],
        )
    except Exception:  # la auditoría nunca debe tumbar la solicitud
        logger.exception("No se pudo escribir el registro de auditoría")
