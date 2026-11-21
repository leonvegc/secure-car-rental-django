"""
Módulo de administración (RESPONSABLE: Josue).
UTN-04 usuarios, UTN-05/06 roles y permisos, UTN-09 visor de auditoría.
Las vistas de abajo son marcadores de la base; Josue las reemplaza.
"""

from django.shortcuts import render

from core.permisos import requiere_permiso, solo_superadmin


@requiere_permiso("usuarios.ver")
def usuarios_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Usuarios"})


@solo_superadmin
@requiere_permiso("roles.ver")
def roles_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Roles y permisos"})


@solo_superadmin
def auditoria_lista(request):
    return render(request, "core/en_construccion.html", {"titulo": "Registro de auditoría"})
