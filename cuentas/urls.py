from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("login/", views.IniciarSesionView.as_view(), name="login"),
    path("logout/", views.CerrarSesionView.as_view(), name="logout"),
]
