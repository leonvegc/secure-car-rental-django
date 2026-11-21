"""
Fixtures compartidas por toda la suite de seguridad (UTN-10).

- Todas las solicitudes se hacen por HTTPS simulado, igual que en Render.
- `cliente_superadmin`, `cliente_auditor`, `cliente_agente`: sesiones ya iniciadas.
- `cliente_anonimo`: sin sesión.
- `cliente_csrf`: sin sesión y con verificación CSRF ESTRICTA (el cliente de
  pruebas normal de Django se salta CSRF; este no).
- `login_csrf(usuario)`: cliente con sesión y CSRF estricto.
"""

import os

import pytest
from django.core.management import call_command
from django.test import Client

from cuentas.models import Usuario

IP_PRUEBA = "203.0.113.10"


class ClienteHTTPS(Client):
    """Cliente de pruebas que SIEMPRE usa HTTPS (como en Render)."""

    def generic(self, method, path, data="", content_type="application/octet-stream", secure=True, **kwargs):
        return super().generic(method, path, data, content_type, secure=True, **kwargs)

CLAVES = {
    "superadmin": os.environ["SEED_SUPERADMIN_PASSWORD"],
    "auditor": os.environ["SEED_AUDITOR_PASSWORD"],
    "agente": os.environ["SEED_AGENTE_PASSWORD"],
}


def nuevo_cliente(csrf=False):
    return ClienteHTTPS(enforce_csrf_checks=csrf, REMOTE_ADDR=IP_PRUEBA)


@pytest.fixture(autouse=True)
def datos_base(db):
    """Permisos, roles y los 3 usuarios de prueba en cada prueba."""
    call_command("seed", "--sin-ejemplos", verbosity=0)


@pytest.fixture
def superadmin():
    return Usuario.objects.get(username="superadmin")


@pytest.fixture
def auditor():
    return Usuario.objects.get(username="auditor")


@pytest.fixture
def agente():
    return Usuario.objects.get(username="agente")


def _con_sesion(usuario, csrf=False):
    c = nuevo_cliente(csrf)
    c.force_login(usuario)
    return c


@pytest.fixture
def cliente_superadmin(superadmin):
    return _con_sesion(superadmin)


@pytest.fixture
def cliente_auditor(auditor):
    return _con_sesion(auditor)


@pytest.fixture
def cliente_agente(agente):
    return _con_sesion(agente)


@pytest.fixture
def cliente_anonimo():
    return nuevo_cliente()


@pytest.fixture
def cliente_csrf():
    return nuevo_cliente(csrf=True)


@pytest.fixture
def login_csrf():
    def _crear(usuario):
        return _con_sesion(usuario, csrf=True)

    return _crear


# Payloads de ataque reutilizables por todos los módulos.
PAYLOADS_SQLI = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "admin'--",
    "' UNION SELECT username, password FROM cuentas_usuario --",
    "1; DROP TABLE vehiculos_vehiculo; --",
]
PAYLOADS_XSS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "\"><svg onload=alert(1)>",
    "javascript:alert(1)",
]
