"""
Pruebas del módulo de Alquileres (Jeremy). Dominio 9: RFD-9.2 a 9.5, RN-9.1 a 9.3.
Cada prueba crea sus datos con el ORM. Los TC-xx siguen la tabla del enunciado.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from alquileres.models import Alquiler
from alquileres.servicios import (
    ReglaNegocioError,
    crear_alquiler,
    registrar_devolucion,
    vehiculos_disponibles,
)
from clientes.models import Cliente
from vehiculos.models import Vehiculo

from .conftest import PAYLOADS_XSS

HOY = timezone.localdate()


def dia(n):
    """Fecha a n días de hoy."""
    return HOY + timedelta(days=n)


def crear_vehiculo(placa="AAA111", estado="DISPONIBLE", tarifa="25000", categoria="SEDAN"):
    return Vehiculo.objects.create(
        placa=placa,
        marca="Toyota",
        modelo="Yaris",
        categoria=categoria,
        tarifa_diaria=Decimal(tarifa),
        estado=estado,
    )


def crear_cliente(cedula="123456789", licencia="LIC12345", vence_en=400):
    return Cliente.objects.create(
        cedula=cedula,
        nombre_completo="Ana Mora",
        numero_licencia=licencia,
        vencimiento_licencia=dia(vence_en),
    )


def alquilar(vehiculo, cliente, usuario, inicio, fin):
    return crear_alquiler(
        cliente=cliente, vehiculo=vehiculo, fecha_inicio=dia(inicio), fecha_fin=dia(fin), usuario=usuario
    )


# 1 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rn91_licencia_vencida_o_que_vence_antes_del_fin_es_rechazada(agente):
    """RN-9.1: una licencia vencida, o que vence antes de fecha_fin, impide el alquiler."""
    vehiculo = crear_vehiculo()
    vencida = crear_cliente(cedula="111111111", licencia="LIC11111", vence_en=-1)
    vence_pronto = crear_cliente(cedula="222222222", licencia="LIC22222", vence_en=3)

    with pytest.raises(ReglaNegocioError, match="licencia"):
        alquilar(vehiculo, vencida, agente, 1, 4)
    with pytest.raises(ReglaNegocioError, match="licencia"):
        alquilar(vehiculo, vence_pronto, agente, 1, 6)  # vence el día 3, el alquiler llega al 6

    assert Alquiler.objects.count() == 0
    vehiculo.refresh_from_db()
    assert vehiculo.estado == "DISPONIBLE"


# 2 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rn92_vehiculo_en_mantenimiento_es_rechazado(agente):
    """RN-9.2: un vehículo en mantenimiento no se puede alquilar."""
    vehiculo = crear_vehiculo(estado="MANTENIMIENTO")
    with pytest.raises(ReglaNegocioError, match="mantenimiento"):
        alquilar(vehiculo, crear_cliente(), agente, 1, 4)
    assert Alquiler.objects.count() == 0


# 3 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rn93_minimo_un_dia_en_el_servicio_y_en_la_base_de_datos(agente):
    """RN-9.3: el alquiler es de mínimo 1 día, en el servicio y en la restricción de la BD."""
    vehiculo, cliente = crear_vehiculo(), crear_cliente()

    with pytest.raises(ReglaNegocioError, match="al menos 1 día"):
        alquilar(vehiculo, cliente, agente, 2, 2)  # fin == inicio
    assert Alquiler.objects.count() == 0

    # Defensa en profundidad: la restricción CHECK de la BD también lo impide.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Alquiler.objects.create(
                cliente=cliente,
                vehiculo=vehiculo,
                fecha_inicio=dia(5),
                fecha_fin=dia(3),
                dias=1,
                tarifa_diaria=Decimal("25000"),
                total=Decimal("25000"),
            )


# 4 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rfd92_total_calculado_vehiculo_alquilado_y_traslape_rechazado(agente):
    """RFD-9.2: el total se calcula en el servidor y no se permiten alquileres traslapados."""
    vehiculo, cliente = crear_vehiculo(tarifa="25000"), crear_cliente()

    alquiler = alquilar(vehiculo, cliente, agente, 1, 4)  # 3 días

    assert alquiler.dias == 3
    assert alquiler.tarifa_diaria == Decimal("25000")
    assert alquiler.total == Decimal("75000")
    assert alquiler.estado == "ACTIVO"
    vehiculo.refresh_from_db()
    assert vehiculo.estado == "ALQUILADO"

    with pytest.raises(ReglaNegocioError, match="ya está alquilado"):
        alquilar(vehiculo, cliente, agente, 3, 6)  # se traslapa con el anterior
    assert Alquiler.objects.count() == 1

    alquilar(vehiculo, cliente, agente, 4, 6)  # pegado al anterior: sí se permite
    assert Alquiler.objects.count() == 2


# 5 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rfd93_devolucion_finaliza_libera_el_vehiculo_y_no_se_repite(agente, superadmin):
    """RFD-9.3: la devolución finaliza el alquiler, libera el vehículo y no se puede repetir."""
    vehiculo = crear_vehiculo()
    alquiler = alquilar(vehiculo, crear_cliente(), agente, 0, 3)

    registrar_devolucion(alquiler=alquiler, usuario=superadmin)

    alquiler.refresh_from_db()
    vehiculo.refresh_from_db()
    assert alquiler.estado == "FINALIZADO"
    assert alquiler.fecha_devolucion is not None
    assert alquiler.recibido_por == superadmin
    assert vehiculo.estado == "DISPONIBLE"

    with pytest.raises(ReglaNegocioError, match="ya fue finalizado"):
        registrar_devolucion(alquiler=alquiler, usuario=superadmin)


# 6 ---------------------------------------------------------------------------
@pytest.mark.negocio
def test_rfd94_disponibilidad_y_rfd95_ingresos_suman_correctamente(agente, cliente_agente):
    """RFD-9.4 y RFD-9.5: la disponibilidad excluye mantenimiento y traslapes; el reporte suma bien."""
    libre = crear_vehiculo("LIBRE1")
    crear_vehiculo("MANT222", estado="MANTENIMIENTO")
    ocupado = crear_vehiculo("OCUP333", tarifa="30000", categoria="SUV")
    cliente = crear_cliente()
    alquilar(ocupado, cliente, agente, 10, 15)  # 5 días * 30000 = 150000

    # Disponibilidad: sin mantenimiento y sin traslapados.
    placas = set(vehiculos_disponibles(dia(12), dia(14)).values_list("placa", flat=True))
    assert placas == {"LIBRE1"}
    placas = set(vehiculos_disponibles(dia(15), dia(18)).values_list("placa", flat=True))
    assert placas == {"LIBRE1", "OCUP333"}  # el alquiler termina el día que empieza la consulta

    # Ingresos: 150000 (SUV) + 75000 (SEDAN) = 225000 en 2 alquileres.
    alquilar(libre, cliente, agente, 1, 4)  # 3 días * 25000 = 75000
    respuesta = cliente_agente.get(
        reverse("alquileres:reporte_ingresos"), {"desde": dia(0).isoformat(), "hasta": dia(30).isoformat()}
    )
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "₡225\xa0000,00" in html
    assert "₡150\xa0000,00" in html and "₡75\xa0000,00" in html  # desglose por categoría
    assert "Cantidad de alquileres: <strong>2</strong>" in html

    # Un rango sin alquileres no suma nada.
    vacio = cliente_agente.get(
        reverse("alquileres:reporte_ingresos"), {"desde": dia(100).isoformat(), "hasta": dia(110).isoformat()}
    )
    assert "₡0,00" in vacio.content.decode()

    # Rangos inválidos se rechazan sin consultar.
    largo = cliente_agente.get(
        reverse("alquileres:reporte_ingresos"), {"desde": dia(0).isoformat(), "hasta": dia(400).isoformat()}
    )
    assert largo.status_code == 200 and "366" in largo.content.decode()


# 7 ---------------------------------------------------------------------------
@pytest.mark.acceso
def test_auditor_recibe_403_en_reporte_lista_y_crear(cliente_auditor):
    """Control de acceso (UTN-05/06): el Auditor no tiene permisos de alquileres y recibe 403."""
    assert cliente_auditor.get(reverse("alquileres:reporte_ingresos")).status_code == 403
    assert cliente_auditor.get(reverse("alquileres:lista")).status_code == 403
    assert cliente_auditor.post(reverse("alquileres:crear"), {}).status_code == 403


# 8 ---------------------------------------------------------------------------
@pytest.mark.sqli
def test_tc02_sqli_en_lista_y_en_disponibilidad_no_da_error_ni_filtra_datos(cliente_agente):
    """TC-02 (SQL Injection): payloads en la búsqueda de la lista y en la fecha de disponibilidad."""
    ataque_lista = "' UNION SELECT username, password FROM cuentas_usuario --"
    respuesta = cliente_agente.get(reverse("alquileres:lista"), {"q": ataque_lista})
    assert respuesta.status_code == 200
    assert "argon2" not in respuesta.content.decode()

    ataque_fecha = "2026-01-01' OR '1'='1"
    respuesta = cliente_agente.get(
        reverse("alquileres:disponibilidad"), {"inicio": ataque_fecha, "fin": dia(5).isoformat()}
    )
    assert respuesta.status_code == 200  # error de formulario, nunca 500
    assert "argon2" not in respuesta.content.decode()


# 9 ---------------------------------------------------------------------------
@pytest.mark.xss
@pytest.mark.parametrize("payload", PAYLOADS_XSS)
def test_tc03_xss_reflejado_en_la_lista_se_escapa(cliente_agente, payload):
    """TC-03 (XSS reflejado): el parámetro q de la lista se escapa en el HTML."""
    respuesta = cliente_agente.get(reverse("alquileres:lista"), {"q": payload[:20]})
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror" not in html
    assert "<svg onload" not in html


# 10 --------------------------------------------------------------------------
@pytest.mark.csrf
def test_devolucion_sin_token_csrf_es_rechazada_y_el_alquiler_sigue_activo(agente, login_csrf):
    """CSRF (UTN-07d): una devolución sin token es rechazada y el alquiler sigue ACTIVO."""
    alquiler = alquilar(crear_vehiculo(), crear_cliente(), agente, 0, 3)

    respuesta = login_csrf(agente).post(reverse("alquileres:devolucion", args=[alquiler.pk]))

    assert respuesta.status_code == 403
    alquiler.refresh_from_db()
    assert alquiler.estado == "ACTIVO"


# 11 --------------------------------------------------------------------------
@pytest.mark.negocio
def test_crear_ignora_total_dias_y_estado_enviados_por_el_usuario(cliente_agente):
    """Asignación masiva: total, días, estado y tarifa enviados por el usuario se ignoran."""
    vehiculo, cliente = crear_vehiculo(tarifa="25000"), crear_cliente()

    respuesta = cliente_agente.post(
        reverse("alquileres:crear"),
        {
            "cliente": cliente.pk,
            "vehiculo": vehiculo.pk,
            "fecha_inicio": dia(1).isoformat(),
            "fecha_fin": dia(4).isoformat(),
            "total": "1",
            "dias": "100",
            "estado": "FINALIZADO",
            "tarifa_diaria": "1",
        },
    )

    assert respuesta.status_code == 302
    alquiler = Alquiler.objects.get()
    assert alquiler.total == Decimal("75000")
    assert alquiler.dias == 3
    assert alquiler.estado == "ACTIVO"
    assert alquiler.tarifa_diaria == Decimal("25000")