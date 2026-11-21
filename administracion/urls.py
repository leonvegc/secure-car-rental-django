from django.urls import path

from . import views

app_name = "administracion"

urlpatterns = [
    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("roles/", views.roles_lista, name="roles_lista"),
    path("auditoria/", views.auditoria_lista, name="auditoria_lista"),
]
