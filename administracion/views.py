"""
Módulo de administración (RESPONSABLE: Josue).
UTN-04 usuarios, UTN-05/06 roles y permisos, UTN-09 visor de auditoría.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso, solo_superadmin
from cuentas.models import Usuario

from .forms import FiltroUsuariosForm, UsuarioCrearForm, UsuarioEditarForm


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


@requiere_permiso("usuarios.crear")
@require_http_methods(["GET", "POST"])
def usuarios_crear(request):
    form = UsuarioCrearForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                usuario = form.save()
        except IntegrityError:
            messages.error(request, "No se pudo guardar el usuario. Revise los datos ingresados.")
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.GESTION_USUARIO,
                detalle=f"Usuario {usuario.username} creado con rol '{usuario.rol.nombre}'",
            )
            messages.success(request, f"Usuario {usuario.username} creado.")
            return redirect("administracion:usuarios_detalle", pk=usuario.pk)
    return render(request, "administracion/usuario_form.html", {"form": form, "titulo": "Nuevo usuario"})


@requiere_permiso("usuarios.editar")
@require_http_methods(["GET", "POST"])
def usuarios_editar(request, pk):
    usuario = get_object_or_404(Usuario.objects.select_related("rol"), pk=pk)
    form = UsuarioEditarForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                usuario = form.save()
        except IntegrityError:
            messages.error(request, "No se pudo actualizar el usuario. Revise los datos ingresados.")
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.GESTION_USUARIO,
                detalle=f"Usuario {usuario.username} editado",
            )
            messages.success(request, f"Usuario {usuario.username} actualizado.")
            return redirect("administracion:usuarios_detalle", pk=usuario.pk)
    return render(
        request,
        "administracion/usuario_form.html",
        {"form": form, "titulo": f"Editar usuario {usuario.username}"},
    )


@solo_superadmin
@requiere_permiso("roles.ver")
def roles_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Roles y permisos"})


@solo_superadmin
def auditoria_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Registro de auditoría"})
