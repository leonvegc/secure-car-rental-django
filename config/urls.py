from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("cuentas/", include("cuentas.urls")),
    path("administracion/", include("administracion.urls")),  # Josue
    path("vehiculos/", include("vehiculos.urls")),  # Stephany
    path("clientes/", include("clientes.urls")),  # Stephany
    path("alquileres/", include("alquileres.urls")),  # Jeremy
]

handler400 = "core.views.error_400"
handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
