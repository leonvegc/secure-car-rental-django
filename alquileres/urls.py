from django.urls import path

from . import views

app_name = "alquileres"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("disponibilidad/", views.disponibilidad, name="disponibilidad"),
    path("reportes/ingresos/", views.reporte_ingresos, name="reporte_ingresos"),
]
