from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.http import require_GET

from .auditoria import registrar_evento
from .models import RegistroAuditoria


@require_GET
def inicio(request):
    return render(request, "core/inicio.html")


@login_not_required
@require_GET
def salud(request):
    """Chequeo de salud para Render. No expone ninguna información."""
    return HttpResponse("ok", content_type="text/plain")


# ---------------------------------------------------------------------------
# Páginas de error: mensajes genéricos, sin trazas ni datos internos (UTN-06).
# ---------------------------------------------------------------------------
def error_400(request, exception=None):
    return render(request, "errores/400.html", status=400)


def error_403(request, exception=None):
    registrar_evento(
        request,
        RegistroAuditoria.Tipo.ACCESO_DENEGADO,
        detalle=str(exception or "")[:300],
    )
    return render(request, "errores/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errores/404.html", status=404)


def error_500(request):
    # Sin contexto de la solicitud: la página de error no debe depender de la BD.
    return HttpResponse(loader.render_to_string("errores/500.html"), status=500)


def csrf_fallido(request, reason=""):
    registrar_evento(request, RegistroAuditoria.Tipo.CSRF_RECHAZADO, detalle=str(reason)[:300])
    return render(request, "errores/403.html", {"es_csrf": True}, status=403)
