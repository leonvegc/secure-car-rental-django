import ipaddress

from django.conf import settings


def _ip_valida(valor):
    try:
        return str(ipaddress.ip_address(valor.strip()))
    except (ValueError, AttributeError):
        return None


def obtener_ip(request):
    """
    IP real del cliente.

    Detrás de un proxy (Render) la IP viene en X-Forwarded-For. Un atacante puede
    agregar valores falsos AL INICIO de ese encabezado, por eso se toma la IP que
    agregó el último proxy de confianza (contando desde la derecha).
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    proxies = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    if xff and proxies > 0:
        partes = [p for p in xff.split(",") if p.strip()]
        if len(partes) >= proxies:
            ip = _ip_valida(partes[-proxies])
            if ip:
                return ip
    return _ip_valida(request.META.get("REMOTE_ADDR", ""))


def obtener_ip_axes(request, *args, **kwargs):
    return obtener_ip(request) or "0.0.0.0"
