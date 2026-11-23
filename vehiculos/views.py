"""
Módulo de Vehículos (UTN-03).

Cada vista exige su permiso antes de hacer cualquier otra cosa y todo acceso
a la base de datos pasa por el ORM.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso

from .forms import FiltroVehiculosForm, VehiculoForm
from .models import Vehiculo


@requiere_permiso("vehiculos.ver")
@require_GET
def lista(request):
    filtro = FiltroVehiculosForm(request.GET)
    consulta = Vehiculo.objects.all()
    parametros = {}

    # Solo se usan los valores ya limpiados; si el formulario es inválido, no se filtra.
    if filtro.is_valid():
        datos = filtro.cleaned_data
        if datos["q"]:
            q = datos["q"]
            consulta = consulta.filter(Q(placa__icontains=q) | Q(marca__icontains=q) | Q(modelo__icontains=q))
        if datos["categoria"]:
            consulta = consulta.filter(categoria=datos["categoria"])
        if datos["estado"]:
            consulta = consulta.filter(estado=datos["estado"])
        parametros = {campo: valor for campo, valor in datos.items() if valor}

    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    contexto = {"filtro": filtro, "pagina": pagina, "parametros_url": urlencode(parametros)}
    return render(request, "vehiculos/lista.html", contexto)


@requiere_permiso("vehiculos.ver")
@require_GET
def detalle(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    return render(request, "vehiculos/detalle.html", {"vehiculo": vehiculo})


def _guardar(request, vehiculo, accion, titulo):
    """Lógica común de crear y editar: muestra el formulario o guarda y audita."""
    datos = request.POST if request.method == "POST" else None
    form = VehiculoForm(datos, instance=vehiculo)
    if form.is_valid():
        try:
            with transaction.atomic():
                vehiculo = form.save()
        except IntegrityError:  # p. ej. otra placa igual guardada al mismo tiempo
            messages.error(request, "No se pudo guardar el vehículo. Revise los datos.")
        else:
            registrar_evento(request, RegistroAuditoria.Tipo.OPERACION, detalle=f"Vehículo {vehiculo.placa} {accion}")
            messages.success(request, f"Vehículo {vehiculo.placa} {accion}.")
            return redirect("vehiculos:detalle", pk=vehiculo.pk)
    return render(request, "vehiculos/form.html", {"form": form, "titulo": titulo})


@requiere_permiso("vehiculos.crear")
@require_http_methods(["GET", "POST"])
def crear(request):
    return _guardar(request, None, "creado", "Nuevo vehículo")


@requiere_permiso("vehiculos.editar")
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    return _guardar(request, vehiculo, "editado", "Editar vehículo")


@requiere_permiso("vehiculos.borrar")
@require_http_methods(["GET", "POST"])
def borrar(request, pk):
    """GET muestra la confirmación; solo el POST (con token CSRF) borra."""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == "POST":
        placa = vehiculo.placa
        try:
            vehiculo.delete()
        except ProtectedError:  # los alquileres usan PROTECT: conservan su historial
            messages.error(request, "No se puede borrar: el vehículo tiene alquileres registrados.")
            return redirect("vehiculos:detalle", pk=pk)
        registrar_evento(request, RegistroAuditoria.Tipo.OPERACION, detalle=f"Vehículo {placa} borrado")
        messages.success(request, f"Vehículo {placa} borrado.")
        return redirect("vehiculos:lista")
    return render(request, "vehiculos/borrar_confirmar.html", {"vehiculo": vehiculo})
