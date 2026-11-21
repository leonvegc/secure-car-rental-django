from django.conf import settings


def seguridad(request):
    usuario = getattr(request, "user", None)
    permisos = usuario.codigos_permiso() if usuario is not None and usuario.is_authenticated else frozenset()
    return {
        "permisos_usuario": permisos,
        "es_superadmin": bool(usuario is not None and usuario.is_authenticated and usuario.es_superadmin),
        "sesion_segundos": settings.SESION_INACTIVIDAD_SEGUNDOS,
    }
