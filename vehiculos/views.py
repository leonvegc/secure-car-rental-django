"""
Módulo de Vehículos (UTN-03).

Cada vista exige su permiso antes de hacer cualquier otra cosa y todo acceso
a la base de datos pasa por el ORM.
"""

from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.permisos import requiere_permiso

from .forms import FiltroVehiculosForm
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
