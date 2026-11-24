from django.urls import path

from . import views

app_name = "administracion"

urlpatterns = [
    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("usuarios/nuevo/", views.usuarios_crear, name="usuarios_crear"),
    path("usuarios/<int:pk>/", views.usuarios_detalle, name="usuarios_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuarios_editar, name="usuarios_editar"),
    path("roles/", views.roles_lista, name="roles_lista"),
    path("auditoria/", views.auditoria_lista, name="auditoria_lista"),
]
