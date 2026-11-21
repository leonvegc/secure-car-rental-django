"""
Módulo de Clientes (RESPONSABLE: Stephany).
La vista de abajo es un marcador de la base; Stephany la reemplaza.
"""

from django.shortcuts import render

from core.permisos import requiere_permiso


@requiere_permiso("clientes.ver")
def lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Clientes"})
