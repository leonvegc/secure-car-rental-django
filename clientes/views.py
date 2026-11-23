"""
Módulo de Clientes (RFD-9.1). DATO SENSIBLE: el número de licencia.

Nunca se escribe la licencia en la auditoría, en una URL ni en un mensaje.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
from core.permisos import requiere_permiso

from .forms import ClienteForm, FiltroClientesForm
from .models import Cliente


@requiere_permiso("clientes.ver")
@require_GET
def lista(request):
    filtro = FiltroClientesForm(request.GET)
    consulta = Cliente.objects.all()
    parametros = {}

    # Si el formulario es inválido no se filtra: nunca se usa request.GET directo.
    if filtro.is_valid() and filtro.cleaned_data["q"]:
        q = filtro.cleaned_data["q"]
        consulta = consulta.filter(Q(cedula__icontains=q) | Q(nombre_completo__icontains=q))
        parametros = {"q": q}

    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    contexto = {
        "filtro": filtro,
        "pagina": pagina,
        "parametros_url": urlencode(parametros),
        "hoy": timezone.localdate(),  # para marcar las licencias vencidas
    }
    return render(request, "clientes/lista.html", contexto)


@requiere_permiso("clientes.ver")
@require_GET
def detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contexto = {
        "cliente": cliente,
        "alquileres": cliente.alquileres.select_related("vehiculo"),  # historial del cliente
        "hoy": timezone.localdate(),
    }
    return render(request, "clientes/detalle.html", contexto)


def _guardar(request, cliente, accion, titulo):
    """Lógica común de crear y editar: muestra el formulario o guarda y audita."""
    datos = request.POST if request.method == "POST" else None
    form = ClienteForm(datos, instance=cliente)
    if form.is_valid():
        try:
            with transaction.atomic():
                cliente = form.save()
        except IntegrityError:  # p. ej. misma cédula guardada al mismo tiempo
            messages.error(request, "No se pudo guardar el cliente. Revise los datos.")
        else:
            registrar_evento(request, RegistroAuditoria.Tipo.OPERACION, detalle=f"Cliente {cliente.cedula} {accion}")
            messages.success(request, f"Cliente {cliente.cedula} {accion}.")
            return redirect("clientes:lista")
    return render(request, "clientes/form.html", {"form": form, "titulo": titulo})


@requiere_permiso("clientes.crear")
@require_http_methods(["GET", "POST"])
def crear(request):
    return _guardar(request, None, "creado", "Nuevo cliente")


@requiere_permiso("clientes.editar")
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return _guardar(request, cliente, "editado", "Editar cliente")
