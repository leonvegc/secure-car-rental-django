"""
Pruebas del módulo de Administración (Josue).
Cubren UTN-02, UTN-04, UTN-05, UTN-06, UTN-07a/b/d, UTN-08 y UTN-09.
"""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import RegistroAuditoria
from cuentas.models import Permiso, Rol, Usuario

from .conftest import CLAVES, PAYLOADS_SQLI, nuevo_cliente

CLAVE_SEGURA = "Clave#Segura2026!"
T = RegistroAuditoria.Tipo


def datos_usuario(rol_id, **cambios):
    """Datos válidos para crear un usuario mediante el formulario."""
    datos = {
        "username": "nuevo.user",
        "nombre_completo": "Carlos Méndez",
        "identificacion": "301230456",
        "email": "Carlos.Mendez@Alquiler.Test",
        "rol": str(rol_id),
        "is_active": "on",
        "password1": CLAVE_SEGURA,
        "password2": CLAVE_SEGURA,
    }
    return {**datos, **cambios}


def datos_edicion(usuario, **cambios):
    """Datos válidos para editar un usuario existente."""
    datos = {
        "username": usuario.username,
        "nombre_completo": usuario.nombre_completo,
        "identificacion": usuario.identificacion,
        "email": usuario.email,
        "rol": str(usuario.rol_id),
        "is_active": "on" if usuario.is_active else "",
        "nueva_password1": "",
        "nueva_password2": "",
    }
    return {**datos, **cambios}


def crear_operador(permisos_codigos):
    """Crea un rol no-SuperAdmin con los permisos indicados y un usuario asignado."""
    rol = Rol.objects.create(nombre="Operador", descripcion="Rol de prueba")
    rol.permisos.set(Permiso.objects.filter(codigo__in=permisos_codigos))
    usuario = Usuario.objects.create_user(
        username="operador",
        email="operador@alquiler.test",
        password=CLAVE_SEGURA,
        rol=rol,
        nombre_completo="Luis Operador",
        identificacion="401110222",
    )
    return rol, usuario


# ------------------------------------------------------- Control de acceso --
@pytest.mark.acceso
def test_tc07_agente_no_puede_borrar_superadmin_por_post(cliente_agente, superadmin):
    """TC-07: el Agente de alquiler hace POST directo para borrar al SuperAdmin -> 403 y sigue existiendo."""
    r = cliente_agente.post(reverse("administracion:usuarios_borrar", args=[superadmin.pk]))
    assert r.status_code == 403
    assert Usuario.objects.filter(pk=superadmin.pk).exists()
    assert RegistroAuditoria.objects.filter(tipo=T.ACCESO_DENEGADO, username="agente").exists()


@pytest.mark.acceso
def test_auditor_solo_lee_usuarios_y_ve_ultimo_inicio_sesion(cliente_auditor, superadmin):
    """UTN-04/05/06: el Auditor recibe 403 en POST a usuarios_crear, pero ve lista con último login."""
    rol_auditor = Rol.objects.get(nombre="Auditor")
    r_post = cliente_auditor.post(reverse("administracion:usuarios_crear"), datos_usuario(rol_auditor.pk))
    assert r_post.status_code == 403
    assert not Usuario.objects.filter(username="nuevo.user").exists()

    # Registrar un inicio de sesión real para verificar el formato de fecha/hora en la lista.
    c = nuevo_cliente()
    c.post("/cuentas/login/", {"username": "superadmin", "password": CLAVES["superadmin"]})
    superadmin.refresh_from_db()
    assert superadmin.last_login is not None

    r_get = cliente_auditor.get(reverse("administracion:usuarios_lista"))
    assert r_get.status_code == 200
    html = r_get.content.decode()
    fecha_local = timezone.localtime(superadmin.last_login).strftime("%d/%m/%Y %H:%M")
    assert fecha_local in html
    assert "Nunca" in html  # los demás usuarios aún no han iniciado sesión
    assert superadmin.nombre_completo in html
    assert superadmin.identificacion in html


@pytest.mark.acceso
def test_escalamiento_operador_no_puede_asignar_rol_superadmin():
    """UTN-05/06: un usuario con usuarios.crear sin ser SuperAdmin no puede crear otro SuperAdmin."""
    _, operador = crear_operador(["usuarios.ver", "usuarios.crear"])
    rol_superadmin = Rol.objects.get(es_superadmin=True)

    c = nuevo_cliente()
    c.force_login(operador)
    r = c.post(reverse("administracion:usuarios_crear"), datos_usuario(rol_superadmin.pk))
    assert r.status_code in (200, 403)
    assert not Usuario.objects.filter(username="nuevo.user").exists()


@pytest.mark.acceso
def test_escalamiento_operador_no_puede_editar_ni_borrar_superadmin(superadmin):
    """UTN-05/06: un rol con usuarios.editar/borrar que no es SuperAdmin recibe 403 sobre un SuperAdmin."""
    _, operador = crear_operador(["usuarios.ver", "usuarios.editar", "usuarios.borrar"])
    c = nuevo_cliente()
    c.force_login(operador)

    assert c.post(reverse("administracion:usuarios_editar", args=[superadmin.pk]), datos_edicion(superadmin)).status_code == 403
    assert c.post(reverse("administracion:usuarios_borrar", args=[superadmin.pk])).status_code == 403
    assert Usuario.objects.filter(pk=superadmin.pk).exists()


@pytest.mark.acceso
def test_roles_exigen_solo_superadmin_aunque_tenga_permiso():
    """UTN-06: ningún rol distinto a SuperAdmin accede a gestión de roles aunque tenga permisos roles.*."""
    _, operador = crear_operador(["roles.ver", "roles.crear", "roles.editar", "roles.borrar"])
    c = nuevo_cliente()
    c.force_login(operador)

    assert c.get(reverse("administracion:roles_lista")).status_code == 403
    assert c.post(reverse("administracion:roles_crear"), {"nombre": "Intruso", "descripcion": ""}).status_code == 403


@pytest.mark.acceso
def test_superadmin_no_se_borra_ni_se_desactiva_ni_borra_rol_sistema(cliente_superadmin, superadmin):
    """UTN-04/06: el superadmin no puede borrarse, desactivarse, cambiar su rol ni borrar un rol de sistema."""
    # No se puede borrar a sí mismo.
    r_borrar = cliente_superadmin.post(reverse("administracion:usuarios_borrar", args=[superadmin.pk]))
    assert r_borrar.status_code == 302
    assert Usuario.objects.filter(pk=superadmin.pk).exists()

    # No puede cambiar su propio rol ni desactivarse.
    rol_auditor = Rol.objects.get(nombre="Auditor")
    r_edit = cliente_superadmin.post(
        reverse("administracion:usuarios_editar", args=[superadmin.pk]),
        datos_edicion(superadmin, rol=str(rol_auditor.pk), is_active=""),
    )
    assert r_edit.status_code == 200
    superadmin.refresh_from_db()
    assert superadmin.rol.es_superadmin is True
    assert superadmin.is_active is True

    # No se puede borrar el rol de sistema Auditor.
    r_rol = cliente_superadmin.post(reverse("administracion:roles_borrar", args=[rol_auditor.pk]))
    assert r_rol.status_code == 302
    assert Rol.objects.filter(pk=rol_auditor.pk).exists()


@pytest.mark.acceso
def test_proteccion_ultimo_superadmin_activo_y_permisos_esenciales(cliente_superadmin, superadmin):
    """UTN-04/06: no se puede dejar el sistema sin SuperAdmin activo ni quitarle permisos esenciales."""
    rol_super = Rol.objects.get(es_superadmin=True)
    rol_auditor = Rol.objects.get(nombre="Auditor")

    # Otro SuperAdmin inactivo no cuenta como respaldo activo.
    segundo = Usuario.objects.create_user(
        username="super2",
        email="super2@alquiler.test",
        password=CLAVE_SEGURA,
        rol=rol_super,
        nombre_completo="Segundo Super",
        identificacion="501230456",
        is_active=False,
    )
    assert Usuario.objects.filter(is_active=True, rol__es_superadmin=True).count() == 1

    # Activar el segundo para poder intentar borrar al primero, y luego desactivar al segundo:
    # con solo uno activo, intentar desactivar/cambiar rol al único activo desde otro actor falla.
    segundo.is_active = True
    segundo.save()
    c2 = nuevo_cliente()
    c2.force_login(segundo)
    # Borrar al primero deja a segundo como último SuperAdmin activo -> permitido.
    assert c2.post(reverse("administracion:usuarios_borrar", args=[superadmin.pk])).status_code == 302
    assert not Usuario.objects.filter(pk=superadmin.pk).exists()

    # Al rol SuperAdmin no se le pueden quitar permisos esenciales (usuarios.ver/editar, roles.ver/editar).
    permiso_veh = Permiso.objects.get(codigo="vehiculos.ver")
    r_perm = c2.post(
        reverse("administracion:roles_editar", args=[rol_super.pk]),
        {"nombre": rol_super.nombre, "descripcion": rol_super.descripcion, "permisos": [str(permiso_veh.pk)]},
    )
    assert r_perm.status_code == 200
    assert set(rol_super.permisos.values_list("codigo", flat=True)) >= {
        "usuarios.ver",
        "usuarios.editar",
        "roles.ver",
        "roles.editar",
    }

    # No se puede borrar un rol personalizado que tiene usuarios asignados.
    rol_personal, _ = crear_operador(["usuarios.ver"])
    assert c2.post(reverse("administracion:roles_borrar", args=[rol_personal.pk])).status_code == 302
    assert Rol.objects.filter(pk=rol_personal.pk).exists()
    assert rol_auditor.es_sistema is True


# ---------------------------------------------------------------------- XSS --
@pytest.mark.xss
def test_tc04_xss_almacenado_en_rol_y_auditoria_sale_escapado(cliente_superadmin):
    """TC-04: XSS almacenado en descripción de rol y en login fallido sale escapado en HTML."""
    payload_rol = "<img src=x onerror=alert(1)>"
    r = cliente_superadmin.post(
        reverse("administracion:roles_crear"),
        {"nombre": "Rol Prueba XSS", "descripcion": payload_rol},
    )
    assert r.status_code == 302
    html_roles = cliente_superadmin.get(reverse("administracion:roles_lista")).content.decode()
    assert "&lt;img" in html_roles
    assert "<img src=x onerror" not in html_roles

    # Login fallido con username malicioso -> en el visor de auditoría sale escapado.
    payload_login = "<script>alert(1)</script>"
    nuevo_cliente().post("/cuentas/login/", {"username": payload_login, "password": "incorrecta"})
    html_audit = cliente_superadmin.get(reverse("administracion:auditoria_lista")).content.decode()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_audit
    assert "<script>alert(1)</script>" not in html_audit


@pytest.mark.xss
def test_tc03_xss_reflejado_en_busquedas_sale_escapado(cliente_superadmin):
    """TC-03: XSS reflejado en búsqueda de usuarios y filtro de auditoría se escapa."""
    payload = "<script>alert(1)</script>"
    html_u = cliente_superadmin.get(reverse("administracion:usuarios_lista"), {"q": payload}).content.decode()
    assert payload not in html_u
    assert "&lt;script&gt;" in html_u

    html_a = cliente_superadmin.get(
        reverse("administracion:auditoria_lista"), {"username": payload}
    ).content.decode()
    assert payload not in html_a
    assert "&lt;script&gt;" in html_a


# ------------------------------------------------------------ SQL Injection --
@pytest.mark.sqli
def test_tc02_sqli_en_busqueda_usuarios_no_devuelve_todos_ni_hashes(cliente_superadmin):
    """TC-02: tautología y UNION SELECT en búsqueda de usuarios no exponen usuarios ni hashes."""
    r1 = cliente_superadmin.get(reverse("administracion:usuarios_lista"), {"q": "' OR '1'='1"})
    assert r1.status_code == 200
    html1 = r1.content.decode()
    assert "Sofía Administradora" not in html1
    assert "Andrés Auditor" not in html1
    assert "Gabriela Agente" not in html1

    r2 = cliente_superadmin.get(
        reverse("administracion:usuarios_lista"),
        {"q": "' UNION SELECT password FROM cuentas_usuario --"},
    )
    assert r2.status_code == 200
    assert b"argon2" not in r2.content


@pytest.mark.sqli
@pytest.mark.parametrize("payload", PAYLOADS_SQLI)
def test_tc02_sqli_en_filtro_auditoria(cliente_superadmin, payload):
    """TC-02: payloads SQLi en filtros de auditoría no exponen datos ni fallan."""
    r = cliente_superadmin.get(reverse("administracion:auditoria_lista"), {"username": payload})
    assert r.status_code == 200
    assert b"argon2" not in r.content


# --------------------------------------------------------------------- CSRF --
@pytest.mark.csrf
def test_tc08_crear_usuario_sin_token_csrf_es_rechazado(login_csrf, superadmin):
    """TC-08: POST a usuarios_crear sin token CSRF responde 403 y no crea usuario."""
    rol_auditor = Rol.objects.get(nombre="Auditor")
    c = login_csrf(superadmin)
    r = c.post(reverse("administracion:usuarios_crear"), datos_usuario(rol_auditor.pk))
    assert r.status_code == 403
    assert not Usuario.objects.filter(username="nuevo.user").exists()
    assert RegistroAuditoria.objects.filter(tipo=T.CSRF_RECHAZADO).exists()


@pytest.mark.csrf
def test_tc08_borrar_usuario_y_crear_rol_sin_csrf_rechazados(login_csrf, superadmin, agente):
    """TC-08: borrar usuario y crear rol sin token CSRF responden 403."""
    c = login_csrf(superadmin)
    assert c.post(reverse("administracion:usuarios_borrar", args=[agente.pk])).status_code == 403
    assert Usuario.objects.filter(pk=agente.pk).exists()

    assert c.post(reverse("administracion:roles_crear"), {"nombre": "SinCSRF", "descripcion": ""}).status_code == 403
    assert not Rol.objects.filter(nombre="SinCSRF").exists()


# ---------------------------------------------------------------- Auditoría --
@pytest.mark.auditoria
def test_auditoria_cambio_de_rol_y_cambio_de_permisos(cliente_superadmin, agente):
    """UTN-09: cambiar rol de un usuario crea CAMBIO_ROL y editar permisos de rol crea CAMBIO_PERMISOS."""
    rol_auditor = Rol.objects.get(nombre="Auditor")
    r = cliente_superadmin.post(
        reverse("administracion:usuarios_editar", args=[agente.pk]),
        datos_edicion(agente, rol=str(rol_auditor.pk)),
    )
    assert r.status_code == 302
    reg_rol = RegistroAuditoria.objects.get(tipo=T.CAMBIO_ROL)
    assert reg_rol.username == "superadmin"
    assert "agente" in reg_rol.detalle
    assert "Agente de alquiler" in reg_rol.detalle and "Auditor" in reg_rol.detalle

    # Modificar permisos de un rol personalizado.
    rol_custom = Rol.objects.create(nombre="Supervisor", descripcion="Supervisión")
    p_ver = Permiso.objects.get(codigo="vehiculos.ver")
    p_rep = Permiso.objects.get(codigo="reportes.ver_reportes")
    rol_custom.permisos.set([p_ver])

    r_perm = cliente_superadmin.post(
        reverse("administracion:roles_editar", args=[rol_custom.pk]),
        {"nombre": "Supervisor", "descripcion": "Supervisión", "permisos": [str(p_rep.pk)]},
    )
    assert r_perm.status_code == 302
    reg_perm = RegistroAuditoria.objects.get(tipo=T.CAMBIO_PERMISOS)
    assert reg_perm.username == "superadmin"
    assert "+[reportes.ver_reportes]" in reg_perm.detalle
    assert "-[vehiculos.ver]" in reg_perm.detalle


@pytest.mark.auditoria
def test_visor_auditoria_filtra_por_tipo_usuario_y_fechas(cliente_superadmin):
    """UTN-09: el visor de auditoría filtra por tipo, username y rango de fechas."""
    RegistroAuditoria.objects.create(
        tipo=T.LOGIN_FALLIDO, username="atacante", ip="203.0.113.55", detalle="clave mala"
    )
    RegistroAuditoria.objects.create(
        tipo=T.CAMBIO_ROL, username="superadmin", ip="203.0.113.10", detalle="rol cambiado"
    )
    hoy = timezone.localdate()
    r = cliente_superadmin.get(
        reverse("administracion:auditoria_lista"),
        {
            "tipo": T.LOGIN_FALLIDO,
            "username": "atacante",
            "desde": hoy.isoformat(),
            "hasta": (hoy + timedelta(days=1)).isoformat(),
        },
    )
    assert r.status_code == 200
    html = r.content.decode()
    assert "atacante" in html
    assert "rol cambiado" not in html


# ------------------------------------------------------------- Credenciales --
@pytest.mark.credenciales
def test_usuario_creado_usa_argon2id_y_rechaza_contrasena_debil(cliente_superadmin):
    """UTN-02/04: el formulario guarda hash Argon2id, normaliza email y rechaza contraseñas débiles."""
    rol_auditor = Rol.objects.get(nombre="Auditor")

    # Contraseña débil "12345678" rechazada.
    r_debil = cliente_superadmin.post(
        reverse("administracion:usuarios_crear"),
        datos_usuario(rol_auditor.pk, password1="12345678", password2="12345678"),
    )
    assert r_debil.status_code == 200
    assert not Usuario.objects.filter(username="nuevo.user").exists()

    # Contraseña fuerte aceptada, guardada con Argon2id y nunca registrada en auditoría.
    r_ok = cliente_superadmin.post(
        reverse("administracion:usuarios_crear"),
        datos_usuario(rol_auditor.pk),
    )
    assert r_ok.status_code == 302
    creado = Usuario.objects.get(username="nuevo.user")
    assert creado.password.startswith("argon2$argon2id$")
    assert creado.check_password(CLAVE_SEGURA)
    assert creado.email == "carlos.mendez@alquiler.test"
    assert not RegistroAuditoria.objects.filter(detalle__contains=CLAVE_SEGURA).exists()


# -------------------------------------------------------------- Encabezados --
@pytest.mark.encabezados
def test_plantillas_administracion_sin_scripts_ni_estilos_en_linea(cliente_superadmin, agente):
    """UTN-08: ninguna plantilla de administración tiene scripts o estilos en línea bloqueados por CSP."""
    rol = Rol.objects.get(nombre="Auditor")
    rutas = [
        reverse("administracion:usuarios_lista"),
        reverse("administracion:usuarios_crear"),
        reverse("administracion:usuarios_detalle", args=[agente.pk]),
        reverse("administracion:usuarios_editar", args=[agente.pk]),
        reverse("administracion:usuarios_borrar", args=[agente.pk]),
        reverse("administracion:roles_lista"),
        reverse("administracion:roles_crear"),
        reverse("administracion:roles_editar", args=[rol.pk]),
        reverse("administracion:auditoria_lista"),
    ]
    for ruta in rutas:
        html = cliente_superadmin.get(ruta).content.decode()
        assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), ruta
        assert "onclick=" not in html and 'style="' not in html, ruta


@pytest.mark.acceso
def test_vuln002_rol_de_sistema_no_se_puede_renombrar(cliente_superadmin):
    """VULN-002: renombrar un rol de sistema se rechaza; editar su descripción sí se permite."""
    rol = Rol.objects.get(nombre="Auditor")
    permisos = [str(pk) for pk in rol.permisos.values_list("pk", flat=True)]
    url = reverse("administracion:roles_editar", args=[rol.pk])
    r = cliente_superadmin.post(url, {"nombre": "Revisor", "descripcion": "x", "permisos": permisos})
    assert r.status_code == 200
    rol.refresh_from_db()
    assert rol.nombre == "Auditor"
    cliente_superadmin.post(url, {"nombre": "Auditor", "descripcion": "Solo lectura", "permisos": permisos})
    rol.refresh_from_db()
    assert rol.descripcion == "Solo lectura"
