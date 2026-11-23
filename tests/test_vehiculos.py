"""
Pruebas del módulo de Vehículos (Stephany). UTN-03 y UTN-07a/b/d.
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
from vehiculos.models import Vehiculo

from .conftest import PAYLOADS_SQLI, PAYLOADS_XSS


def crear_vehiculo(placa="AAA111", estado="DISPONIBLE", **extra):
    datos = dict(marca="Toyota", modelo="Yaris", categoria="SEDAN", tarifa_diaria=Decimal("25000"))
    return Vehiculo.objects.create(placa=placa, estado=estado, **{**datos, **extra})


def datos_form(**cambios):
    """Datos válidos de un POST de vehículo; cada prueba cambia solo lo que ataca."""
    datos = dict(placa="NEW-001", marca="Kia", modelo="Rio", categoria="SEDAN", tarifa_diaria="30000", estado="DISPONIBLE")
    return {**datos, **cambios}


def crear_alquiler_activo(vehiculo):
    hoy = timezone.localdate()
    cliente = Cliente.objects.create(
        cedula="111111111", nombre_completo="Ana Mora", numero_licencia="LIC-1111", vencimiento_licencia=hoy + timedelta(days=300)
    )
    return Alquiler.objects.create(
        cliente=cliente, vehiculo=vehiculo, fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=2), dias=2,
        tarifa_diaria=vehiculo.tarifa_diaria, total=vehiculo.tarifa_diaria * 2, estado=Alquiler.Estado.ACTIVO,
    )


# ------------------------------------------------------------ SQL Injection --
@pytest.mark.sqli
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc02_sqli_en_busqueda_no_expone_datos(cliente_agente, payload):
    """TC-02: ' UNION SELECT ... y otros payloads en la búsqueda no exponen hashes ni dañan la tabla."""
    crear_vehiculo()
    r = cliente_agente.get(reverse("vehiculos:lista"), {"q": payload})
    assert r.status_code == 200
    assert b"argon2" not in r.content
    assert Vehiculo.objects.count() == 1  # el DROP TABLE no se ejecutó


@pytest.mark.sqli
@pytest.mark.parametrize("payload", ["' OR '1'='1", "' OR 1=1 --"])
def test_tc02_sqli_tautologia_no_devuelve_todo(cliente_agente, payload):
    """TC-02: una tautología se busca como texto literal; no coincide con ningún vehículo."""
    crear_vehiculo(placa="AAA111")
    r = cliente_agente.get(reverse("vehiculos:lista"), {"q": payload})
    assert r.status_code == 200
    assert b"AAA111" not in r.content


# ---------------------------------------------------------------------- XSS --
@pytest.mark.xss
@pytest.mark.parametrize("payload", [p for p in PAYLOADS_XSS if "<" in p])
def test_tc04_xss_almacenado_sale_escapado(cliente_agente, payload):
    """TC-04: un payload guardado (por ORM, saltando el validador) se escapa en la lista y el detalle."""
    v = crear_vehiculo(modelo=payload)
    for url in (reverse("vehiculos:lista"), reverse("vehiculos:detalle", args=[v.pk])):
        html = cliente_agente.get(url).content.decode()
        assert payload not in html
        assert "&lt;" in html


@pytest.mark.xss
def test_tc03_xss_reflejado_en_busqueda_sale_escapado(cliente_agente):
    """TC-03: el texto buscado se muestra escapado en el formulario, sin ejecutarse."""
    payload = "<script>alert(1)</script>"
    html = cliente_agente.get(reverse("vehiculos:lista"), {"q": payload}).content.decode()
    assert payload not in html
    assert "&lt;script&gt;" in html


@pytest.mark.xss
@pytest.mark.parametrize("campo", ["marca", "modelo"])
def test_xss_en_formulario_es_rechazado(cliente_agente, campo):
    """UTN-07b: el validador rechaza < y > al crear; el vehículo no se guarda."""
    r = cliente_agente.post(reverse("vehiculos:crear"), datos_form(**{campo: "<script>alert(1)</script>"}))
    assert r.status_code == 200  # vuelve al formulario con el error
    assert b"<script>alert(1)" not in r.content
    assert not Vehiculo.objects.exists()


# ------------------------------------------------------------------- Acceso --
@pytest.mark.acceso
def test_tc06_auditor_solo_lee_vehiculos(cliente_auditor):
    """UTN-05/06: el Auditor ve lista y detalle (200); crear, editar y borrar dan 403 y no cambian nada."""
    v = crear_vehiculo()
    assert cliente_auditor.get(reverse("vehiculos:lista")).status_code == 200
    assert cliente_auditor.get(reverse("vehiculos:detalle", args=[v.pk])).status_code == 200

    assert cliente_auditor.get(reverse("vehiculos:crear")).status_code == 403
    assert cliente_auditor.post(reverse("vehiculos:crear"), datos_form()).status_code == 403
    assert cliente_auditor.post(reverse("vehiculos:editar", args=[v.pk]), datos_form(placa="AAA111")).status_code == 403
    assert cliente_auditor.post(reverse("vehiculos:borrar", args=[v.pk])).status_code == 403

    assert Vehiculo.objects.count() == 1
    v.refresh_from_db()
    assert v.marca == "Toyota"


@pytest.mark.acceso
def test_anonimo_es_enviado_al_login(cliente_anonimo):
    """UTN-07c: sin sesión no se accede a ninguna ruta de vehículos."""
    r = cliente_anonimo.get(reverse("vehiculos:lista"))
    assert r.status_code == 302 and "/cuentas/login/" in r.url


# --------------------------------------------------------------------- CSRF --
@pytest.mark.csrf
def test_tc08_borrar_sin_token_csrf_es_rechazado(login_csrf, agente):
    """TC-08: un POST a borrar sin token CSRF responde 403 y el vehículo sigue existiendo."""
    v = crear_vehiculo()
    r = login_csrf(agente).post(reverse("vehiculos:borrar", args=[v.pk]))
    assert r.status_code == 403
    assert Vehiculo.objects.filter(pk=v.pk).exists()


@pytest.mark.csrf
def test_tc08_crear_sin_token_csrf_es_rechazado(login_csrf, agente):
    """TC-08: un POST a crear sin token CSRF responde 403 y no crea nada."""
    r = login_csrf(agente).post(reverse("vehiculos:crear"), datos_form())
    assert r.status_code == 403
    assert not Vehiculo.objects.exists()


@pytest.mark.csrf
def test_formularios_de_vehiculos_incluyen_token_csrf(cliente_agente):
    """UTN-07d: crear, editar y la confirmación de borrar traen {% csrf_token %}."""
    v = crear_vehiculo()
    for nombre, args in (("crear", []), ("editar", [v.pk]), ("borrar", [v.pk])):
        html = cliente_agente.get(reverse(f"vehiculos:{nombre}", args=args)).content
        principal = html.split(b"<main")[1]  # el menú ya trae un token (Salir): se mira solo el contenido
        assert b"csrfmiddlewaretoken" in principal, nombre


# ------------------------------------------------------------------ Negocio --
@pytest.mark.negocio
def test_crear_vehiculo_valido_normaliza_y_audita(cliente_agente):
    """UTN-03: la placa se guarda en mayúscula y sin espacios, y la creación queda en la auditoría."""
    r = cliente_agente.post(reverse("vehiculos:crear"), datos_form(placa=" new-001 "))
    assert r.status_code == 302
    assert Vehiculo.objects.get().placa == "NEW-001"
    assert RegistroAuditoria.objects.filter(tipo=RegistroAuditoria.Tipo.OPERACION, detalle="Vehículo NEW-001 creado").exists()


@pytest.mark.negocio
def test_placa_duplicada_es_rechazada(cliente_agente):
    """UTN-03: no se repite la placa, aunque llegue en minúscula."""
    crear_vehiculo(placa="AAA111")
    r = cliente_agente.post(reverse("vehiculos:crear"), datos_form(placa="aaa111"))
    assert r.status_code == 200
    assert "Ya existe un vehículo con esa placa." in r.content.decode()
    assert Vehiculo.objects.count() == 1


@pytest.mark.negocio
@pytest.mark.parametrize("tarifa", ["0", "-5000", "abc"])
def test_tarifa_invalida_es_rechazada(cliente_agente, tarifa):
    """UTN-03: la tarifa debe ser un número mayor que cero."""
    r = cliente_agente.post(reverse("vehiculos:crear"), datos_form(tarifa_diaria=tarifa))
    assert r.status_code == 200
    assert not Vehiculo.objects.exists()


@pytest.mark.negocio
def test_estado_alquilado_no_se_asigna_desde_el_formulario(cliente_agente):
    """Solo el módulo de alquileres pone ALQUILADO; el formulario lo rechaza."""
    r = cliente_agente.post(reverse("vehiculos:crear"), datos_form(estado="ALQUILADO"))
    assert r.status_code == 200
    assert not Vehiculo.objects.exists()


@pytest.mark.negocio
def test_vehiculo_alquilado_conserva_su_estado_al_editar(cliente_agente):
    """Un vehículo ALQUILADO se puede editar, pero el estado enviado se ignora."""
    v = crear_vehiculo(estado="ALQUILADO")
    datos = datos_form(placa="AAA111", tarifa_diaria="31000", estado="DISPONIBLE")
    assert cliente_agente.post(reverse("vehiculos:editar", args=[v.pk]), datos).status_code == 302
    v.refresh_from_db()
    assert v.estado == "ALQUILADO" and v.tarifa_diaria == Decimal("31000")


@pytest.mark.negocio
def test_no_pasa_a_mantenimiento_con_alquiler_activo(cliente_agente):
    """Regla de negocio: un vehículo con alquiler ACTIVO no puede pasar a MANTENIMIENTO."""
    v = crear_vehiculo()
    crear_alquiler_activo(v)
    datos = datos_form(placa="AAA111", estado="MANTENIMIENTO")
    r = cliente_agente.post(reverse("vehiculos:editar", args=[v.pk]), datos)
    assert r.status_code == 200
    v.refresh_from_db()
    assert v.estado == "DISPONIBLE"


@pytest.mark.negocio
def test_borrar_vehiculo_con_alquileres_muestra_mensaje(cliente_agente):
    """Los alquileres usan PROTECT: no se borra el vehículo y se muestra un mensaje amable."""
    v = crear_vehiculo()
    crear_alquiler_activo(v)
    r = cliente_agente.post(reverse("vehiculos:borrar", args=[v.pk]), follow=True)
    assert "No se puede borrar: el vehículo tiene alquileres registrados." in r.content.decode()
    assert Vehiculo.objects.filter(pk=v.pk).exists()


@pytest.mark.negocio
def test_borrar_solo_por_post_y_queda_auditado(cliente_agente):
    """UTN-03: el GET solo pide confirmación; el POST borra y registra el evento."""
    v = crear_vehiculo()
    url = reverse("vehiculos:borrar", args=[v.pk])
    assert cliente_agente.get(url).status_code == 200
    assert Vehiculo.objects.filter(pk=v.pk).exists()

    assert cliente_agente.post(url).status_code == 302
    assert not Vehiculo.objects.filter(pk=v.pk).exists()
    assert RegistroAuditoria.objects.filter(detalle="Vehículo AAA111 borrado").exists()
