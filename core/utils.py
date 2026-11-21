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

    1. Si CLIENT_IP_HEADER está configurado (Render: True-Client-IP), se usa ese.
    2. Si no, X-Forwarded-For. Un atacante puede
    agregar valores falsos AL INICIO de ese encabezado, por eso se toma la IP que
    agregó el último proxy de confianza (contando desde la derecha).
    """
    # En Render siempre hay Cloudflare delante: True-Client-IP lo pone Cloudflare
    # con la IP real y el cliente no puede falsificarlo (CLIENT_IP_HEADER).
    cabecera = getattr(settings, "CLIENT_IP_HEADER", "")
    if cabecera:
        clave = "HTTP_" + cabecera.upper().replace("-", "_")
        ip = _ip_valida(request.META.get(clave, ""))
        if ip:
            return ip

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
