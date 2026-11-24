"""
Módulo de administración (RESPONSABLE: Josue).
UTN-04 usuarios, UTN-05/06 roles y permisos, UTN-09 visor de auditoría.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso, solo_superadmin
from cuentas.models import Rol, Usuario

from .forms import FiltroUsuariosForm, RolForm, UsuarioCrearForm, UsuarioEditarForm
from .servicios import es_ultimo_superadmin_activo, resumen_cambios_permisos


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
    form = UsuarioCrearForm(request.POST or None, actor=request.user)
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
    if usuario.rol.es_superadmin and not request.user.es_superadmin:
        raise PermissionDenied("Solo un SuperAdmin puede editar cuentas SuperAdmin.")
    rol_anterior = usuario.rol.nombre
    form = UsuarioEditarForm(request.POST or None, instance=usuario, actor=request.user)
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
            if rol_anterior != usuario.rol.nombre:
                registrar_evento(
                    request,
                    RegistroAuditoria.Tipo.CAMBIO_ROL,
                    detalle=f"Usuario {usuario.username}: rol '{rol_anterior}' -> '{usuario.rol.nombre}'",
                )
            messages.success(request, f"Usuario {usuario.username} actualizado.")
            return redirect("administracion:usuarios_detalle", pk=usuario.pk)
    return render(
        request,
        "administracion/usuario_form.html",
        {"form": form, "titulo": f"Editar usuario {usuario.username}"},
    )


@requiere_permiso("usuarios.borrar")
@require_http_methods(["GET", "POST"])
def usuarios_borrar(request, pk):
    """GET muestra la confirmación; solo el POST (con token CSRF) borra."""
    usuario = get_object_or_404(Usuario.objects.select_related("rol"), pk=pk)
    if usuario.rol.es_superadmin and not request.user.es_superadmin:
        raise PermissionDenied("Solo un SuperAdmin puede borrar cuentas SuperAdmin.")

    if usuario.pk == request.user.pk:
        messages.error(request, "No puede borrar su propia cuenta.")
        return redirect("administracion:usuarios_detalle", pk=usuario.pk)

    if es_ultimo_superadmin_activo(usuario):
        messages.error(request, "No se puede borrar al último SuperAdmin activo del sistema.")
        return redirect("administracion:usuarios_detalle", pk=usuario.pk)

    if request.method == "POST":
        username = usuario.username
        try:
            with transaction.atomic():
                if es_ultimo_superadmin_activo(usuario):
                    messages.error(request, "No se puede borrar al último SuperAdmin activo del sistema.")
                    return redirect("administracion:usuarios_detalle", pk=usuario.pk)
                usuario.delete()
        except ProtectedError:
            messages.error(request, "No se puede borrar el usuario porque tiene registros asociados.")
            return redirect("administracion:usuarios_detalle", pk=pk)
        registrar_evento(
            request,
            RegistroAuditoria.Tipo.GESTION_USUARIO,
            detalle=f"Usuario {username} borrado",
        )
        messages.success(request, f"Usuario {username} borrado.")
        return redirect("administracion:usuarios_lista")

    return render(request, "administracion/usuario_borrar_confirmar.html", {"usuario": usuario})


@solo_superadmin
@requiere_permiso("roles.ver")
@require_GET
def roles_lista(request):
    roles = Rol.objects.annotate(cantidad_usuarios=Count("usuarios", distinct=True)).prefetch_related("permisos")
    return render(request, "administracion/roles_lista.html", {"roles": roles})


@solo_superadmin
@requiere_permiso("roles.crear")
@require_http_methods(["GET", "POST"])
def roles_crear(request):
    form = RolForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                rol = form.save()
        except IntegrityError:
            messages.error(request, "No se pudo guardar el rol. Revise los datos ingresados.")
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.GESTION_ROL,
                detalle=f"Rol {rol.nombre} creado",
            )
            permisos_nuevos = set(rol.permisos.values_list("codigo", flat=True))
            if permisos_nuevos:
                agregados, quitados = resumen_cambios_permisos(set(), permisos_nuevos)
                registrar_evento(
                    request,
                    RegistroAuditoria.Tipo.CAMBIO_PERMISOS,
                    detalle=f"Rol {rol}: +[{agregados}] -[{quitados}]",
                )
            messages.success(request, f"Rol {rol.nombre} creado.")
            return redirect("administracion:roles_lista")
    return render(request, "administracion/rol_form.html", {"form": form, "titulo": "Nuevo rol"})


@solo_superadmin
@requiere_permiso("roles.editar")
@require_http_methods(["GET", "POST"])
def roles_editar(request, pk):
    rol = get_object_or_404(Rol.objects.prefetch_related("permisos"), pk=pk)
    permisos_antes = set(rol.permisos.values_list("codigo", flat=True))
    form = RolForm(request.POST or None, instance=rol)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                rol = form.save()
        except IntegrityError:
            messages.error(request, "No se pudo actualizar el rol. Revise los datos ingresados.")
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.GESTION_ROL,
                detalle=f"Rol {rol.nombre} editado",
            )
            permisos_despues = set(rol.permisos.values_list("codigo", flat=True))
            if permisos_antes != permisos_despues:
                agregados, quitados = resumen_cambios_permisos(permisos_antes, permisos_despues)
                registrar_evento(
                    request,
                    RegistroAuditoria.Tipo.CAMBIO_PERMISOS,
                    detalle=f"Rol {rol}: +[{agregados}] -[{quitados}]",
                )
            messages.success(request, f"Rol {rol.nombre} actualizado.")
            return redirect("administracion:roles_lista")
    return render(
        request,
        "administracion/rol_form.html",
        {"form": form, "titulo": f"Editar rol {rol.nombre}"},
    )


@solo_superadmin
@requiere_permiso("roles.borrar")
@require_http_methods(["GET", "POST"])
def roles_borrar(request, pk):
    """GET muestra la confirmación; solo el POST (con token CSRF) borra."""
    rol = get_object_or_404(Rol, pk=pk)

    if rol.es_sistema:
        messages.error(request, "No se puede borrar un rol del sistema.")
        return redirect("administracion:roles_lista")

    if rol.usuarios.exists():
        messages.error(request, "No se puede borrar el rol porque tiene usuarios asignados.")
        return redirect("administracion:roles_lista")

    if request.method == "POST":
        nombre = rol.nombre
        try:
            with transaction.atomic():
                rol.delete()
        except ProtectedError:
            messages.error(request, "No se puede borrar el rol porque tiene usuarios asignados.")
            return redirect("administracion:roles_lista")
        registrar_evento(
            request,
            RegistroAuditoria.Tipo.GESTION_ROL,
            detalle=f"Rol {nombre} borrado",
        )
        messages.success(request, f"Rol {nombre} borrado.")
        return redirect("administracion:roles_lista")

    return render(request, "administracion/rol_borrar_confirmar.html", {"rol": rol})


@solo_superadmin
def auditoria_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Registro de auditoría"})
