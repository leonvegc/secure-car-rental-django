"""
Módulo de administración (RESPONSABLE: Josue).
UTN-04 usuarios, UTN-05/06 roles y permisos, UTN-09 visor de auditoría.
"""

from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.permisos import requiere_permiso, solo_superadmin
from cuentas.models import Usuario

from .forms import FiltroUsuariosForm


@requiere_permiso("usuarios.ver")
@require_GET
def usuarios_lista(request):
    filtro = FiltroUsuariosForm(request.GET)
    consulta = Usuario.objects.select_related("rol").prefetch_related("rol__permisos")
    parametros = {}

    if filtro.is_valid() and filtro.cleaned_data["q"]:
        q = filtro.cleaned_data["q"]
        consulta = consulta.filter(Q(username__icontains=q) | Q(nombre_completo__icontains=q))
        parametros = {"q": q}

    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    contexto = {
        "filtro": filtro,
        "pagina": pagina,
        "parametros_url": urlencode(parametros),
    }
    return render(request, "administracion/usuarios_lista.html", contexto)


@requiere_permiso("usuarios.ver")
@require_GET
def usuarios_detalle(request, pk):
    usuario = get_object_or_404(
        Usuario.objects.select_related("rol").prefetch_related("rol__permisos"),
        pk=pk,
    )
    return render(request, "administracion/usuarios_detalle.html", {"usuario": usuario})


@solo_superadmin
@requiere_permiso("roles.ver")
def roles_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Roles y permisos"})


@solo_superadmin
def auditoria_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Registro de auditoría"})
