"""
Módulo de Alquileres (RESPONSABLE: Jeremy). RFD-9.2 a 9.5.

Las vistas solo reciben la solicitud, validan con formularios y llaman a
alquileres/servicios.py, donde vive la lógica de negocio. Cada vista exige un
permiso ANTES de cualquier otra cosa (el decorador de permiso va por fuera).
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso

from .forms import CrearAlquilerForm, FiltroAlquileresForm
from .models import Alquiler
from .servicios import ReglaNegocioError, anular_alquiler, crear_alquiler, registrar_devolucion


def _alquileres():
    return Alquiler.objects.select_related("cliente", "vehiculo", "registrado_por", "recibido_por")


@requiere_permiso("alquileres.ver")
@require_GET
def lista(request):
    filtro = FiltroAlquileresForm(request.GET)
    consulta = _alquileres()
    parametros = {}
    if filtro.is_valid():
        estado = filtro.cleaned_data["estado"]
        q = filtro.cleaned_data["q"]
        if estado:
            consulta = consulta.filter(estado=estado)
            parametros["estado"] = estado
        if q:
            consulta = consulta.filter(Q(codigo__icontains=q) | Q(vehiculo__placa__icontains=q))
            parametros["q"] = q
    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    contexto = {"filtro": filtro, "pagina": pagina, "parametros_url": urlencode(parametros)}
    return render(request, "alquileres/lista.html", contexto)


@requiere_permiso("alquileres.ver")
@require_GET
def detalle(request, pk):
    alquiler = get_object_or_404(_alquileres(), pk=pk)
    return render(request, "alquileres/detalle.html", {"alquiler": alquiler})


@requiere_permiso("alquileres.crear")
@require_http_methods(["GET", "POST"])
def crear(request):
    form = CrearAlquilerForm(request.POST) if request.method == "POST" else CrearAlquilerForm()
    if request.method == "POST" and form.is_valid():
        try:
            alquiler = crear_alquiler(
                cliente=form.cleaned_data["cliente"],
                vehiculo=form.cleaned_data["vehiculo"],
                fecha_inicio=form.cleaned_data["fecha_inicio"],
                fecha_fin=form.cleaned_data["fecha_fin"],
                usuario=request.user,
            )
        except ReglaNegocioError as error:
            form.add_error(None, str(error))
        except IntegrityError:
            form.add_error(None, "No se pudo registrar el alquiler. Revise los datos e intente de nuevo.")
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.OPERACION,
                detalle=(
                    f"Alquiler {alquiler.codigo} creado: {alquiler.vehiculo.placa}, "
                    f"{alquiler.dias} días, total {alquiler.total}"
                ),
            )
            messages.success(request, f"Alquiler {alquiler.codigo} registrado.")
            return redirect("alquileres:detalle", pk=alquiler.pk)
    return render(request, "alquileres/crear.html", {"form": form})


@requiere_permiso("alquileres.editar")
@require_http_methods(["GET", "POST"])
def devolucion(request, pk):
    alquiler = get_object_or_404(_alquileres(), pk=pk)
    if alquiler.estado != Alquiler.Estado.ACTIVO:
        messages.error(request, "Este alquiler ya fue finalizado.")
        return redirect("alquileres:detalle", pk=alquiler.pk)
    if request.method == "POST":
        try:
            registrar_devolucion(alquiler=alquiler, usuario=request.user)
        except ReglaNegocioError as error:
            messages.error(request, str(error))
        else:
            registrar_evento(
                request,
                RegistroAuditoria.Tipo.OPERACION,
                detalle=f"Alquiler {alquiler.codigo} devuelto: {alquiler.vehiculo.placa}",
            )
            messages.success(request, f"Devolución del alquiler {alquiler.codigo} registrada.")
        return redirect("alquileres:detalle", pk=alquiler.pk)
    return render(request, "alquileres/devolucion_confirmar.html", {"alquiler": alquiler})


@requiere_permiso("alquileres.borrar")
@require_POST
def anular(request, pk):
    alquiler = get_object_or_404(_alquileres(), pk=pk)
    codigo, placa = alquiler.codigo, alquiler.vehiculo.placa
    try:
        anular_alquiler(alquiler=alquiler, usuario=request.user)
    except ReglaNegocioError as error:
        messages.error(request, str(error))
        return redirect("alquileres:detalle", pk=pk)
    registrar_evento(request, RegistroAuditoria.Tipo.OPERACION, detalle=f"Alquiler {codigo} anulado: {placa}")
    messages.success(request, f"Alquiler {codigo} anulado.")
    return redirect("alquileres:lista")


# Marcadores: se reemplazan en los pasos 5 (disponibilidad) y 6 (ingresos).
@requiere_permiso("alquileres.ver")
def disponibilidad(request):
    return render(request, "core/en_construccion.html", {"titulo": "Disponibilidad"})


@requiere_permiso("reportes.ver_reportes")
def reporte_ingresos(request):
    return render(request, "core/en_construccion.html", {"titulo": "Reporte de ingresos"})