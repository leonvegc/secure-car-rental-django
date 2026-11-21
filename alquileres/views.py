"""
Módulo de Alquileres (RESPONSABLE: Jeremy).
RFD-9.2 a 9.5. Las vistas de abajo son marcadores de la base; Jeremy las reemplaza.
"""

from django.shortcuts import render

from core.permisos import requiere_permiso


@requiere_permiso("alquileres.ver")
def lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Alquileres"})


@requiere_permiso("alquileres.ver")
def disponibilidad(request):
    return render(request, "core/en_construccion.html", {"titulo": "Disponibilidad"})


@requiere_permiso("reportes.ver_reportes")
def reporte_ingresos(request):
    return render(request, "core/en_construccion.html", {"titulo": "Reporte de ingresos"})
