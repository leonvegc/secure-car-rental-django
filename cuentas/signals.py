"""UTN-09: registro de inicios de sesión exitosos, fallidos, bloqueos y cierres."""

from axes.signals import user_locked_out
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria


@receiver(user_logged_in)
def al_iniciar_sesion(sender, request, user, **kwargs):
    # Django ya actualiza user.last_login (UTN-04) con su propia señal.
    registrar_evento(request, RegistroAuditoria.Tipo.LOGIN_OK, usuario=user)


@receiver(user_login_failed)
def al_fallar_inicio(sender, credentials, request=None, **kwargs):
    registrar_evento(
        request,
        RegistroAuditoria.Tipo.LOGIN_FALLIDO,
        usuario=None,
        username=(credentials or {}).get("username", ""),
        detalle="Credenciales inválidas",
    )


@receiver(user_locked_out)
def al_bloquear(sender, request, username=None, ip_address=None, **kwargs):
    registrar_evento(
        request,
        RegistroAuditoria.Tipo.BLOQUEO,
        usuario=None,
        username=username or "",
        detalle="Demasiados intentos fallidos; bloqueo temporal",
    )


@receiver(user_logged_out)
def al_cerrar_sesion(sender, request, user, **kwargs):
    if user is not None:
        registrar_evento(request, RegistroAuditoria.Tipo.LOGOUT, usuario=user)
