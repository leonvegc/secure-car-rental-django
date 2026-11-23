from django.urls import path

from . import views

app_name = "alquileres"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.crear, name="crear"),
    path("disponibilidad/", views.disponibilidad, name="disponibilidad"),
    path("reportes/ingresos/", views.reporte_ingresos, name="reporte_ingresos"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/devolucion/", views.devolucion, name="devolucion"),
    path("<int:pk>/anular/", views.anular, name="anular"),
]