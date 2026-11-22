"""
Módulo de Alquileres (RESPONSABLE: Jeremy). RFD-9.2 a 9.5.

Las vistas solo reciben la solicitud, validan con formularios y llaman a
alquileres/servicios.py, donde vive la lógica de negocio. Cada vista exige un
permiso ANTES de cualquier otra cosa (el decorador de permiso va por fuera).
"""

from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso
from vehiculos.models import Vehiculo

from .forms import CrearAlquilerForm, DisponibilidadForm, FiltroAlquileresForm, ReporteIngresosForm
from .models import Alquiler
from .servicios import (
    ReglaNegocioError,
    anular_alquiler,
    crear_alquiler,
    registrar_devolucion,
    vehiculos_disponibles,
)


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


@requiere_permiso("alquileres.ver")
@require_GET
def disponibilidad(request):
    """RFD-9.4: vehículos disponibles en un rango de fechas (formulario GET)."""
    consultado = "inicio" in request.GET or "fin" in request.GET
    form = DisponibilidadForm(request.GET) if consultado else DisponibilidadForm()
    contexto = {"form": form, "resultados": None}
    if consultado and form.is_valid():
        inicio, fin = form.cleaned_data["inicio"], form.cleaned_data["fin"]
        dias = (fin - inicio).days
        vehiculos = vehiculos_disponibles(inicio, fin).order_by("placa")
        contexto.update(
            inicio=inicio,
            fin=fin,
            dias=dias,
            resultados=[{"vehiculo": v, "total_estimado": v.tarifa_diaria * dias} for v in vehiculos],
        )
    return render(request, "alquileres/disponibilidad.html", contexto)


MAX_FILAS_DETALLE = 200


@requiere_permiso("reportes.ver_reportes")
@require_GET
def reporte_ingresos(request):
    """
    RFD-9.5: ingresos de los alquileres cuya fecha de inicio cae en el rango.
    Es un dato sensible del negocio: solo reportes.ver_reportes (el Auditor no).
    """
    consultado = "desde" in request.GET or "hasta" in request.GET
    form = ReporteIngresosForm(request.GET) if consultado else ReporteIngresosForm()
    contexto = {"form": form, "reporte": None}
    if consultado and form.is_valid():
        desde, hasta = form.cleaned_data["desde"], form.cleaned_data["hasta"]
        alquileres = _alquileres().filter(fecha_inicio__gte=desde, fecha_inicio__lte=hasta)
        resumen = alquileres.aggregate(total=Sum("total"), cantidad=Count("id"))
        etiquetas = dict(Vehiculo._meta.get_field("categoria").flatchoices)
        por_categoria = [
            {"categoria": etiquetas.get(fila["vehiculo__categoria"], fila["vehiculo__categoria"]), **fila}
            for fila in alquileres.order_by()
            .values("vehiculo__categoria")
            .annotate(total=Sum("total"), cantidad=Count("id"))
            .order_by("vehiculo__categoria")
        ]
        contexto["reporte"] = {
            "desde": desde,
            "hasta": hasta,
            "total": resumen["total"] or Decimal("0"),
            "cantidad": resumen["cantidad"],
            "por_categoria": por_categoria,
            "detalle": alquileres.order_by("fecha_inicio", "codigo")[:MAX_FILAS_DETALLE],
            "recortado": resumen["cantidad"] > MAX_FILAS_DETALLE,
            "max_filas": MAX_FILAS_DETALLE,
        }
    return render(request, "alquileres/reporte_ingresos.html", contexto)