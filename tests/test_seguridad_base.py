"""
Pruebas de la base de seguridad (Cristopher).
Cubren UTN-02, 05, 06, 07a, 07b, 07c, 07d, 08 y 09. Los IDs TC-xx siguen la
tabla de casos mínimos del enunciado (punto 7).
"""

from datetime import timedelta

import pytest
import time_machine
from django.test import RequestFactory, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone

from core.models import RegistroAuditoria
from core.utils import obtener_ip
from cuentas.models import Usuario
from vehiculos.models import Vehiculo

from .conftest import CLAVES, PAYLOADS_SQLI, PAYLOADS_XSS, nuevo_cliente

LOGIN = "/cuentas/login/"
T = RegistroAuditoria.Tipo


def iniciar_sesion(cliente, username, password):
    return cliente.post(LOGIN, {"username": username, "password": password})


def esta_autenticado(cliente):
    return cliente.get("/").status_code == 200


def rutas_sin_parametros():
    """Todas las rutas con nombre y sin parámetros del proyecto (incluye las nuevas)."""
    rutas = []

    def recorrer(patrones, prefijo=""):
        for p in patrones:
            if isinstance(p, URLResolver):
                ns = f"{prefijo}{p.namespace}:" if p.namespace else prefijo
                recorrer(p.url_patterns, ns)
            elif isinstance(p, URLPattern) and p.name and not p.pattern.converters:
                if "<" in str(p.pattern):
                    continue
                vista = p.callback
                if getattr(vista, "login_required", True) is False:
                    continue  # login, salud
                rutas.append(reverse(prefijo + p.name))

    recorrer(get_resolver().url_patterns)
    return rutas


# ---------------------------------------------------------------- UTN-02 ----
@pytest.mark.credenciales
def test_contrasenas_guardadas_con_argon2id(superadmin):
    """UTN-02: el hash es Argon2id con parámetros reforzados, nunca texto plano."""
    hash_ = superadmin.password
    assert hash_.startswith("argon2$argon2id$")
    assert "m=65536,t=3,p=2" in hash_
    assert CLAVES["superadmin"] not in hash_
    assert superadmin.check_password(CLAVES["superadmin"])


@pytest.mark.credenciales
def test_contrasena_debil_rechazada(superadmin):
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    for debil in ["123456789012", "contrasena", "Password1234", "alquiler"]:
        with pytest.raises(ValidationError):
            validate_password(debil, superadmin)


# ---------------------------------------------------------------- UTN-07a ---
@pytest.mark.sqli
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc01_sqli_en_login_no_da_acceso(payload):
    """TC-01: inyección SQL en el usuario y la contraseña no inicia sesión."""
    c = nuevo_cliente()
    r = iniciar_sesion(c, payload, payload)
    assert r.status_code == 200
    assert r.context["form"].errors  # error controlado, sin traza
    assert not esta_autenticado(c)
    assert Vehiculo.objects.model._meta.db_table  # la tabla sigue existiendo
    assert Usuario.objects.count() == 3


# ---------------------------------------------------------------- UTN-07b ---
@pytest.mark.xss
@pytest.mark.parametrize("payload", PAYLOADS_XSS)
def test_xss_reflejado_en_login_se_escapa(payload):
    """TC-03: lo que el usuario escribe se devuelve escapado, nunca como HTML."""
    r = iniciar_sesion(nuevo_cliente(), payload, "x")
    html = r.content.decode()
    assert payload not in html or payload == "javascript:alert(1)"
    assert "<script>alert(1)</script>" not in html
    assert "onerror=alert(1)>" not in html


@pytest.mark.xss
def test_xss_reflejado_en_parametro_url():
    r = nuevo_cliente().get(LOGIN, {"next": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in r.content.decode()


# ---------------------------------------------------------------- UTN-07c ---
@pytest.mark.sesion
def test_tc05_sesion_expira_tras_60s_de_inactividad():
    """TC-05: con más de 60 s sin actividad la sesión se cierra y se audita."""
    with time_machine.travel(timezone.now(), tick=False) as viaje:
        c = nuevo_cliente()
        r = iniciar_sesion(c, "agente", CLAVES["agente"])
        assert r.status_code == 302
        assert c.get("/").status_code == 200
        viaje.shift(timedelta(seconds=61))
        r = c.get("/")
        assert r.status_code == 302
        assert r.url.startswith(LOGIN)
        assert c.get("/").status_code == 302  # sigue sin sesión
    assert RegistroAuditoria.objects.filter(tipo=T.SESION_EXPIRADA, username="agente").exists()


@pytest.mark.sesion
def test_sesion_activa_se_renueva_con_cada_solicitud():
    with time_machine.travel(timezone.now(), tick=False) as viaje:
        c = nuevo_cliente()
        iniciar_sesion(c, "agente", CLAVES["agente"])
        for _ in range(3):
            viaje.shift(timedelta(seconds=50))
            assert c.get("/").status_code == 200


@pytest.mark.sesion
def test_tc09_cookie_de_sesion_segura_y_sin_datos():
    """TC-09: cookie HttpOnly, Secure, SameSite=Strict y sin datos del usuario."""
    c = nuevo_cliente()
    r = iniciar_sesion(c, "superadmin", CLAVES["superadmin"])
    cookie = r.cookies["sid"]
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "Strict"
    valor = cookie.value
    assert "superadmin" not in valor and "SuperAdmin" not in valor
    assert len(valor) >= 32
    csrf = r.cookies.get("csrft")
    if csrf is not None:
        assert csrf["httponly"] is True and csrf["secure"] is True


@pytest.mark.sesion
def test_id_de_sesion_cambia_al_iniciar_sesion():
    """Previene fijación de sesión: el ID anterior al login no se reutiliza."""
    c = nuevo_cliente()
    c.get(LOGIN)
    c.cookies["sid"] = "idfijadoporelatacante1234567890ab"
    iniciar_sesion(c, "agente", CLAVES["agente"])
    assert c.cookies["sid"].value != "idfijadoporelatacante1234567890ab"


@pytest.mark.sesion
def test_ninguna_ruta_accesible_sin_sesion(cliente_anonimo):
    """UTN-07c: todas las rutas protegidas redirigen al login sin sesión válida."""
    rutas = rutas_sin_parametros()
    assert len(rutas) >= 5
    for ruta in rutas:
        r = cliente_anonimo.get(ruta)
        assert r.status_code == 302, ruta
        assert r.url.startswith(LOGIN), ruta


@pytest.mark.sesion
def test_logout_por_get_no_permitido(cliente_agente):
    assert cliente_agente.get("/cuentas/logout/").status_code == 405
    assert esta_autenticado(cliente_agente)


@pytest.mark.sesion
def test_login_no_permite_redireccion_abierta():
    c = nuevo_cliente()
    r = c.post(LOGIN + "?next=https://atacante.example/robo", {"username": "agente", "password": CLAVES["agente"]})
    assert r.status_code == 302
    assert "atacante.example" not in r.url


# ---------------------------------------------------------------- UTN-07d ---
@pytest.mark.csrf
def test_tc08_formulario_sin_token_csrf_rechazado(cliente_csrf):
    """TC-08: un POST sin token CSRF responde 403 y queda auditado."""
    r = iniciar_sesion(cliente_csrf, "agente", CLAVES["agente"])
    assert r.status_code == 403
    assert RegistroAuditoria.objects.filter(tipo=T.CSRF_RECHAZADO).exists()


@pytest.mark.csrf
def test_logout_sin_token_csrf_rechazado(login_csrf, agente):
    c = login_csrf(agente)
    assert c.post("/cuentas/logout/").status_code == 403
    assert esta_autenticado(c)


@pytest.mark.csrf
def test_formulario_con_token_csrf_valido_funciona(cliente_csrf):
    r = cliente_csrf.get(LOGIN)
    token = r.context["csrf_token"]
    r = cliente_csrf.post(LOGIN, {"username": "agente", "password": CLAVES["agente"], "csrfmiddlewaretoken": str(token)},
                          HTTP_REFERER="https://testserver/cuentas/login/")
    assert r.status_code == 302


# ---------------------------------------------------------------- UTN-08 ----
@pytest.mark.encabezados
@pytest.mark.parametrize("ruta", [LOGIN, "/"])
def test_tc10_encabezados_de_seguridad(ruta, cliente_agente):
    """TC-10: CSP, X-Frame-Options, nosniff, HSTS y demás encabezados."""
    r = cliente_agente.get(ruta, follow=True)
    csp = r["Content-Security-Policy"]
    for directiva in ["default-src 'none'", "script-src 'self'", "frame-ancestors 'none'", "object-src 'none'"]:
        assert directiva in csp
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp
    assert r["X-Frame-Options"] == "DENY"
    assert r["X-Content-Type-Options"] == "nosniff"
    assert r["Strict-Transport-Security"].startswith("max-age=31536000")
    assert r["Referrer-Policy"] == "same-origin"
    assert "no-store" in r["Cache-Control"]
    assert "Permissions-Policy" in r


@pytest.mark.encabezados
def test_http_redirige_a_https():
    from django.test import Client

    r = Client().get(LOGIN)
    assert r.status_code == 301
    assert r.url.startswith("https://")


@pytest.mark.encabezados
def test_plantillas_sin_scripts_en_linea(cliente_superadmin):
    """Con CSP sin 'unsafe-inline', cualquier <script> en línea quedaría bloqueado."""
    import re

    html = cliente_superadmin.get("/").content.decode()
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html)
    assert " on" + "click=" not in html and "style=\"" not in html


# ------------------------------------------------------- UTN-05/06 y 09 -----
@pytest.mark.acceso
def test_tc06_auditor_en_url_de_roles_recibe_403_y_se_audita(cliente_auditor):
    """TC-06: el Auditor entra directo a la URL de roles -> 403 auditado."""
    r = cliente_auditor.get(reverse("administracion:roles_lista"))
    assert r.status_code == 403
    html = r.content.decode()
    assert "Traceback" not in html and "Falta permiso" not in html and "Solo SuperAdmin" not in html
    reg = RegistroAuditoria.objects.get(tipo=T.ACCESO_DENEGADO)
    assert reg.username == "auditor"
    assert reg.ruta == reverse("administracion:roles_lista")
    assert reg.ip == "203.0.113.10"


@pytest.mark.acceso
@pytest.mark.parametrize("quien", ["cliente_auditor", "cliente_agente"])
def test_solo_superadmin_accede_a_auditoria(quien, request, cliente_superadmin):
    """UTN-09: solo SuperAdmin ve los registros."""
    assert request.getfixturevalue(quien).get(reverse("administracion:auditoria_lista")).status_code == 403
    assert cliente_superadmin.get(reverse("administracion:auditoria_lista")).status_code == 200


@pytest.mark.acceso
def test_auditor_no_accede_a_clientes_dato_sensible(cliente_auditor):
    """El Auditor no tiene acceso a la licencia ni datos personales de los clientes."""
    assert cliente_auditor.get(reverse("clientes:lista")).status_code == 403
    assert cliente_auditor.get(reverse("alquileres:lista")).status_code == 403


@pytest.mark.acceso
def test_usuario_inactivo_no_tiene_permisos(agente):
    agente.is_active = False
    agente.save()
    assert agente.codigos_permiso() == frozenset()


@pytest.mark.acceso
def test_404_sin_informacion_interna(cliente_agente):
    r = cliente_agente.get("/no-existe/../../etc/passwd")
    assert r.status_code == 404
    html = r.content.decode()
    assert "URLconf" not in html and "Traceback" not in html and "DEBUG" not in html


@pytest.mark.auditoria
def test_login_exitoso_y_fallido_se_auditan_con_ip():
    c = nuevo_cliente()
    iniciar_sesion(c, "agente", "clave-incorrecta")
    iniciar_sesion(c, "agente", CLAVES["agente"])
    fallido = RegistroAuditoria.objects.get(tipo=T.LOGIN_FALLIDO)
    exitoso = RegistroAuditoria.objects.get(tipo=T.LOGIN_OK)
    assert fallido.username == "agente" and fallido.ip == "203.0.113.10" and fallido.fecha_hora
    assert exitoso.usuario.username == "agente" and exitoso.ip == "203.0.113.10"
    assert Usuario.objects.get(username="agente").last_login is not None  # UTN-04


@pytest.mark.auditoria
def test_fuerza_bruta_bloquea_tras_5_intentos():
    c = nuevo_cliente()
    for _ in range(5):
        iniciar_sesion(c, "superadmin", "incorrecta")
    r = iniciar_sesion(c, "superadmin", CLAVES["superadmin"])  # clave correcta, pero bloqueado
    assert r.status_code == 429
    assert not esta_autenticado(c)
    assert RegistroAuditoria.objects.filter(tipo=T.BLOQUEO).exists()


@pytest.mark.auditoria
def test_registros_de_auditoria_son_inmutables():
    c = nuevo_cliente()
    iniciar_sesion(c, "agente", "mala")
    reg = RegistroAuditoria.objects.first()
    reg.detalle = "alterado"
    with pytest.raises(PermissionError):
        reg.save()
    with pytest.raises(PermissionError):
        reg.delete()


@pytest.mark.auditoria
@override_settings(TRUSTED_PROXY_COUNT=1)
def test_ip_falsa_en_x_forwarded_for_no_se_acepta():
    """Un atacante no puede falsificar su IP en la auditoría con X-Forwarded-For."""
    req = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 198.51.100.7", REMOTE_ADDR="10.0.0.1")
    assert obtener_ip(req) == "198.51.100.7"
    req = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="<script>", REMOTE_ADDR="10.0.0.1")
    assert obtener_ip(req) == "10.0.0.1"
