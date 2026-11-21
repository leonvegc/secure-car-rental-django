from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from .forms import LoginForm


@method_decorator([login_not_required, sensitive_post_parameters("password"), never_cache], name="dispatch")
class IniciarSesionView(auth_views.LoginView):
    template_name = "cuentas/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sesion_expirada"] = self.request.GET.get("expirada") == "1"
        return ctx


class CerrarSesionView(auth_views.LogoutView):
    """Solo acepta POST con token CSRF (Django rechaza GET con 405)."""

    http_method_names = ["post", "options"]
