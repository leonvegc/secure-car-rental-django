import time

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from .auditoria import registrar_evento
from .models import RegistroAuditoria

CLAVE_ACTIVIDAD = "_ultima_actividad"


class InactividadSesionMiddleware:
    """
    UTN-07c: invalida la sesión tras SESION_INACTIVIDAD_SEGUNDOS sin solicitudes.

    Es una segunda barrera además de SESSION_COOKIE_AGE: la marca de tiempo se
    guarda del lado del servidor, así que manipular la cookie no extiende la sesión.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ahora = time.time()
            ultima = request.session.get(CLAVE_ACTIVIDAD)
            limite = settings.SESION_INACTIVIDAD_SEGUNDOS
            if ultima is not None and ahora - float(ultima) > limite:
                usuario = request.user
                logout(request)  # borra la sesión en BD y rota la cookie
                registrar_evento(
                    request,
                    RegistroAuditoria.Tipo.SESION_EXPIRADA,
                    usuario=usuario,
                    detalle=f"Inactividad mayor a {limite} s",
                )
                return redirect(f"{reverse(settings.LOGIN_URL)}?expirada=1")
            request.session[CLAVE_ACTIVIDAD] = ahora
        return self.get_response(request)


class EncabezadosSeguridadMiddleware:
    """UTN-08: encabezados adicionales a los que ya agrega Django."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        # No guardar en caché páginas con datos (evita verlos con "Atrás" tras cerrar sesión).
        # (Los estáticos los responde WhiteNoise antes de llegar aquí.)
        response["Cache-Control"] = "no-store, max-age=0"
        response["Pragma"] = "no-cache"
        return response
