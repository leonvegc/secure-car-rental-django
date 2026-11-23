"""
Pruebas del módulo de Clientes (Stephany). RFD-9.1 y protección del dato sensible (licencia).
Cada prueba crea sus datos con el ORM. Los TC-xx siguen la tabla del enunciado.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from alquileres.models import Alquiler
from clientes.models import Cliente
from core.models import RegistroAuditoria
from cuentas.models import Permiso, Rol, Usuario
from vehiculos.models import Vehiculo

from .conftest import PAYLOADS_SQLI, PAYLOADS_XSS, nuevo_cliente

HOY = timezone.localdate()


def crear_cliente(cedula="200000001", licencia="LIC-0001", vence_en=400, nombre="Laura Pérez"):
    return Cliente.objects.create(
        cedula=cedula, nombre_completo=nombre, numero_licencia=licencia, vencimiento_licencia=HOY + timedelta(days=vence_en)
    )


def datos_form(**cambios):
    """Datos válidos de un POST de cliente; cada prueba cambia solo lo que ataca."""
    datos = dict(
        cedula="301110222", nombre_completo="Pedro Soto", numero_licencia="LIC-9999",
        vencimiento_licencia=str(HOY + timedelta(days=400)), telefono="88887777", correo="pedro@cliente.test",
    )
    return {**datos, **cambios}


def crear_alquiler(cliente, estado=Alquiler.Estado.ACTIVO):
    vehiculo = Vehiculo.objects.create(
        placa="AAA111", marca="Toyota", modelo="Yaris", categoria="SEDAN", tarifa_diaria=Decimal("25000")
    )
    return Alquiler.objects.create(
        cliente=cliente, vehiculo=vehiculo, fecha_inicio=HOY, fecha_fin=HOY + timedelta(days=2), dias=2,
        tarifa_diaria=vehiculo.tarifa_diaria, total=vehiculo.tarifa_diaria * 2, estado=estado,
    )


@pytest.fixture
def cliente_lector():
    """Usuario con clientes.ver pero SIN clientes.editar: no debe ver la licencia completa."""
    rol = Rol.objects.create(nombre="Lector de clientes")
    rol.permisos.add(Permiso.objects.get(codigo="clientes.ver"))
    usuario = Usuario.objects.create_user(
        "lector", "lector@test.local", "Lector#Clave2026!", rol, nombre_completo="Lector Uno", identificacion="900000001"
    )
    cliente = nuevo_cliente()
    cliente.force_login(usuario)
    return cliente


# ------------------------------------------------------------ SQL Injection --
@pytest.mark.sqli
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc02_sqli_en_busqueda_no_expone_datos(cliente_agente, payload):
    """TC-02: payloads SQL en la búsqueda no exponen hashes ni dañan la tabla."""
    crear_cliente()
    r = cliente_agente.get(reverse("clientes:lista"), {"q": payload})
    assert r.status_code == 200
    assert b"argon2" not in r.content
    assert Cliente.objects.count() == 1


@pytest.mark.sqli
@pytest.mark.parametrize("payload", ["' OR '1'='1", "' OR 1=1 --"])
def test_tc02_sqli_tautologia_no_devuelve_todo(cliente_agente, payload):
    """TC-02: una tautología se busca como texto literal; no coincide con ningún cliente."""
    crear_cliente(nombre="Laura Pérez")
    r = cliente_agente.get(reverse("clientes:lista"), {"q": payload})
    assert r.status_code == 200
    assert "Laura" not in r.content.decode()


# ---------------------------------------------------------------------- XSS --
@pytest.mark.xss
@pytest.mark.parametrize("payload", [p for p in PAYLOADS_XSS if "<" in p])
def test_tc04_xss_almacenado_sale_escapado(cliente_agente, payload):
    """TC-04: un payload guardado (por ORM, saltando el validador) se escapa en la lista y el detalle."""
    c = crear_cliente(nombre=payload)
    for url in (reverse("clientes:lista"), reverse("clientes:detalle", args=[c.pk])):
        html = cliente_agente.get(url).content.decode()
        assert payload not in html
        assert "&lt;" in html


@pytest.mark.xss
def test_tc03_xss_reflejado_en_busqueda_sale_escapado(cliente_agente):
    """TC-03: el texto buscado se muestra escapado en el formulario, sin ejecutarse."""
    payload = "<script>alert(1)</script>"
    html = cliente_agente.get(reverse("clientes:lista"), {"q": payload}).content.decode()
    assert payload not in html
    assert "&lt;script&gt;" in html


@pytest.mark.xss
@pytest.mark.parametrize("campo", ["nombre_completo", "numero_licencia"])
def test_xss_en_formulario_es_rechazado(cliente_agente, campo):
    """UTN-07b: el validador rechaza < y > al crear; el cliente no se guarda."""
    r = cliente_agente.post(reverse("clientes:crear"), datos_form(**{campo: "<script>alert(1)</script>"}))
    assert r.status_code == 200  # vuelve al formulario con el error
    assert b"<script>alert(1)" not in r.content
    assert not Cliente.objects.exists()


# ------------------------------------------------------------------- Acceso --
@pytest.mark.acceso
def test_tc06_auditor_no_accede_a_clientes(cliente_auditor):
    """UTN-06: el Auditor no tiene clientes.ver; toda ruta de clientes responde 403 y no cambia nada."""
    c = crear_cliente()
    assert cliente_auditor.get(reverse("clientes:lista")).status_code == 403
    assert cliente_auditor.get(reverse("clientes:detalle", args=[c.pk])).status_code == 403
    assert cliente_auditor.get(reverse("clientes:crear")).status_code == 403
    assert cliente_auditor.post(reverse("clientes:crear"), datos_form()).status_code == 403
    assert cliente_auditor.post(reverse("clientes:editar", args=[c.pk]), datos_form(cedula="200000001")).status_code == 403
    assert cliente_auditor.post(reverse("clientes:borrar", args=[c.pk])).status_code == 403
    assert Cliente.objects.count() == 1


@pytest.mark.acceso
def test_usuario_sin_permiso_de_edicion_no_ve_la_licencia_completa(cliente_lector):
    """Dato sensible: con clientes.ver pero sin clientes.editar, el detalle muestra la licencia enmascarada."""
    c = crear_cliente(licencia="LIC-0001")
    html = cliente_lector.get(reverse("clientes:detalle", args=[c.pk])).content.decode()
    assert "****0001" in html
    assert "LIC-0001" not in html
    assert "Editar" not in html


@pytest.mark.acceso
def test_usuario_sin_permisos_de_escritura_recibe_403(cliente_lector):
    """UTN-05: con solo clientes.ver, crear, editar y borrar por POST directo dan 403."""
    c = crear_cliente()
    assert cliente_lector.post(reverse("clientes:crear"), datos_form()).status_code == 403
    assert cliente_lector.post(reverse("clientes:editar", args=[c.pk]), datos_form(cedula="200000001")).status_code == 403
    assert cliente_lector.post(reverse("clientes:borrar", args=[c.pk])).status_code == 403
    assert Cliente.objects.count() == 1


@pytest.mark.acceso
def test_anonimo_es_enviado_al_login(cliente_anonimo):
    """UTN-07c: sin sesión no se accede a ninguna ruta de clientes."""
    r = cliente_anonimo.get(reverse("clientes:lista"))
    assert r.status_code == 302 and "/cuentas/login/" in r.url


# --------------------------------------------------------------------- CSRF --
@pytest.mark.csrf
def test_tc08_crear_y_borrar_sin_token_csrf_son_rechazados(login_csrf, agente):
    """TC-08: un POST sin token CSRF responde 403 y no crea ni borra clientes."""
    c = crear_cliente()
    sesion = login_csrf(agente)
    assert sesion.post(reverse("clientes:crear"), datos_form()).status_code == 403
    assert sesion.post(reverse("clientes:borrar", args=[c.pk])).status_code == 403
    assert Cliente.objects.count() == 1


@pytest.mark.csrf
def test_formularios_de_clientes_incluyen_token_csrf(cliente_agente):
    """UTN-07d: crear, editar y la confirmación de borrar traen {% csrf_token %}."""
    c = crear_cliente()
    for nombre, args in (("crear", []), ("editar", [c.pk]), ("borrar", [c.pk])):
        html = cliente_agente.get(reverse(f"clientes:{nombre}", args=args)).content
        principal = html.split(b"<main")[1]  # el menú ya trae un token (Salir): se mira solo el contenido
        assert b"csrfmiddlewaretoken" in principal, nombre


# ------------------------------------------------------------------ Negocio --
@pytest.mark.negocio
def test_rfd91_registro_de_cliente_guarda_licencia_normalizada(cliente_agente):
    """RFD-9.1: se registra con cédula, licencia y vencimiento; la licencia queda en mayúscula y sin espacios."""
    r = cliente_agente.post(reverse("clientes:crear"), datos_form(numero_licencia=" lic-9999 "))
    assert r.status_code == 302
    cliente = Cliente.objects.get()
    assert cliente.cedula == "301110222"
    assert cliente.numero_licencia == "LIC-9999"


@pytest.mark.negocio
def test_rfd91_cedula_duplicada_es_rechazada(cliente_agente):
    """RFD-9.1: la cédula no se repite y el mensaje es claro."""
    crear_cliente(cedula="301110222")
    r = cliente_agente.post(reverse("clientes:crear"), datos_form(cedula="301110222"))
    assert r.status_code == 200
    assert "Ya existe un cliente con esa cédula." in r.content.decode()
    assert Cliente.objects.count() == 1


@pytest.mark.negocio
@pytest.mark.parametrize(
    "cambio",
    [
        {"cedula": "12345"},
        {"cedula": "ABC123456"},
        {"numero_licencia": "AB"},
        {"telefono": "123"},
        {"correo": "no-es-un-correo"},
        {"vencimiento_licencia": "no-es-fecha"},
    ],
)
def test_rfd91_datos_invalidos_son_rechazados(cliente_agente, cambio):
    """RFD-9.1: cédula, licencia, teléfono, correo y fecha se validan antes de guardar."""
    r = cliente_agente.post(reverse("clientes:crear"), datos_form(**cambio))
    assert r.status_code == 200
    assert not Cliente.objects.exists()


@pytest.mark.negocio
def test_licencia_enmascarada_en_la_lista(cliente_agente):
    """Dato sensible: en la lista LIC-0001 aparece como ****0001 y nunca completa."""
    crear_cliente(licencia="LIC-0001")
    html = cliente_agente.get(reverse("clientes:lista")).content.decode()
    assert "****0001" in html
    assert "LIC-0001" not in html


@pytest.mark.negocio
def test_detalle_muestra_licencia_completa_solo_con_permiso_de_edicion(cliente_agente):
    """El Agente (tiene clientes.editar) ve la licencia completa en el detalle."""
    c = crear_cliente(licencia="LIC-0001")
    html = cliente_agente.get(reverse("clientes:detalle", args=[c.pk])).content.decode()
    assert "LIC-0001" in html


@pytest.mark.negocio
def test_detalle_muestra_historial_de_alquileres(cliente_agente):
    """RFD-9.1: el detalle del cliente lista sus alquileres (código, vehículo y estado)."""
    c = crear_cliente()
    alquiler = crear_alquiler(c)
    html = cliente_agente.get(reverse("clientes:detalle", args=[c.pk])).content.decode()
    assert alquiler.codigo in html
    assert "AAA111" in html


@pytest.mark.negocio
def test_licencia_vencida_se_marca_en_la_lista(cliente_agente):
    """Una licencia vencida lleva la clase 'vencida'; una vigente no."""
    crear_cliente(cedula="111111111", licencia="LIC-1111", vence_en=-1)
    assert 'class="vencida"' in cliente_agente.get(reverse("clientes:lista")).content.decode()
    Cliente.objects.all().delete()
    crear_cliente(cedula="222222222", licencia="LIC-2222", vence_en=30)
    assert 'class="vencida"' not in cliente_agente.get(reverse("clientes:lista")).content.decode()


@pytest.mark.negocio
def test_licencia_no_aparece_en_auditoria_ni_en_urls(cliente_agente):
    """La licencia nunca va en la auditoría ni en las URLs: crear, editar y borrar solo registran la cédula."""
    r = cliente_agente.post(reverse("clientes:crear"), datos_form(numero_licencia="LIC-9999"))
    assert "9999" not in r.url
    cliente = Cliente.objects.get()
    cliente_agente.post(reverse("clientes:editar", args=[cliente.pk]), datos_form(numero_licencia="LIC-8888"))
    cliente_agente.post(reverse("clientes:borrar", args=[cliente.pk]))

    detalles = list(RegistroAuditoria.objects.filter(tipo=RegistroAuditoria.Tipo.OPERACION).values_list("detalle", flat=True))
    assert sorted(detalles) == ["Cliente 301110222 borrado", "Cliente 301110222 creado", "Cliente 301110222 editado"]


@pytest.mark.negocio
def test_borrar_cliente_con_alquileres_muestra_mensaje_sin_licencia(cliente_agente):
    """Los alquileres usan PROTECT: no se borra el cliente y el mensaje no revela datos sensibles."""
    c = crear_cliente(licencia="LIC-0001")
    crear_alquiler(c)
    r = cliente_agente.post(reverse("clientes:borrar", args=[c.pk]), follow=True)
    mensajes = r.content.decode().split('<ul class="mensajes">')[1].split("</ul>")[0]  # el detalle sí muestra la licencia
    assert "No se puede borrar: el cliente tiene alquileres registrados." in mensajes
    assert "LIC" not in mensajes and c.cedula not in mensajes
    assert Cliente.objects.filter(pk=c.pk).exists()


@pytest.mark.negocio
def test_borrar_solo_por_post(cliente_agente):
    """El GET solo pide confirmación; el POST borra."""
    c = crear_cliente()
    url = reverse("clientes:borrar", args=[c.pk])
    assert cliente_agente.get(url).status_code == 200
    assert Cliente.objects.filter(pk=c.pk).exists()
    assert cliente_agente.post(url).status_code == 302
    assert not Cliente.objects.filter(pk=c.pk).exists()
