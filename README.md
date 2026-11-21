# Secure Car Rental (Django)

> Hardened car rental web app built with Django 6 and PostgreSQL. It has role-based access control, Argon2id password hashing, brute-force lockout, a 60-second session timeout, CSRF protection and a strict Content-Security-Policy, plus an immutable audit log and an automated security test suite (pytest, HTML/XML reports). It was built to withstand a cross-team penetration test.

**Course project:** ISW-622 Software Testing, Universidad Técnica Nacional (Costa Rica). The documentation below is in Spanish.

---

## Alquiler de Vehículos — Sistema web seguro (ISW-622, Proyecto 2)

Dominio 9 — **Alquiler de vehículos**. Entidad principal: **Vehículo**. Rol operativo: **Agente de alquiler**.

**Equipo:** Cristopher, Josue, Stephany, Jeremy.

**Stack:** Python 3.13, Django 6.0, PostgreSQL 16, Gunicorn y WhiteNoise. Se publica en Render.
Se eligió Django porque trae protecciones nativas: un ORM parametrizado, plantillas con escape automático, CSRF, CSP, hashers Argon2 y control de sesión.

- Arquitectura de seguridad: [`docs/ARQUITECTURA_SEGURIDAD.md`](docs/ARQUITECTURA_SEGURIDAD.md)
- Reglas del equipo: [`docs/CONTRATO_EQUIPO.md`](docs/CONTRATO_EQUIPO.md)

## Ambiente publicado

- URL: _(se completa al publicar en Render)_
- El plan gratuito de Render apaga el servicio tras 15 minutos sin uso. La primera solicitud puede tardar unos 50 segundos en responder.

## Credenciales de prueba (datos ficticios)

| Rol | Usuario | Contraseña local (DEBUG=1) | Contraseña en el ambiente publicado |
|---|---|---|---|
| SuperAdmin | `superadmin` | `Super#Admin2026!` | _(se entrega al equipo evaluador)_ |
| Auditor | `auditor` | `Audit#Lectura2026!` | _(se entrega al equipo evaluador)_ |
| Agente de alquiler | `agente` | `Agente#Alquila2026!` | _(se entrega al equipo evaluador)_ |

Tras 5 intentos fallidos, la combinación de usuario e IP queda bloqueada 15 minutos.

## Instalación local

```bash
git clone <url-del-repo> && cd secure-car-rental-django
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux/macOS:           source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
python manage.py migrate
python manage.py seed         # permisos, roles, usuarios de prueba y datos de ejemplo
python manage.py runserver
```

Abra http://127.0.0.1:8000. Sin `DATABASE_URL` se usa SQLite local. Para usar PostgreSQL, defina `DATABASE_URL`.

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DEBUG` | `1` solo en desarrollo | `0` |
| `SECRET_KEY` | Clave secreta de Django (obligatoria en producción) | — |
| `DATABASE_URL` | `postgres://usuario:clave@host:5432/bd` | SQLite si DEBUG=1 |
| `DB_SSL_REQUIRE` | Exigir SSL a la BD | `1` en producción |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por comas | `localhost,127.0.0.1` |
| `USAR_HTTPS` | Redirección HTTPS, HSTS y cookies Secure | `1` en producción |
| `SESION_INACTIVIDAD_SEGUNDOS` | Tiempo máximo de inactividad | `60` |
| `TRUSTED_PROXY_COUNT` | Proxies de confianza (Render = 1) | `1` |
| `AXES_FAILURE_LIMIT` / `AXES_COOLOFF_MINUTOS` | Bloqueo por fuerza bruta | `5` / `15` |
| `SEED_SUPERADMIN_PASSWORD`, `SEED_AUDITOR_PASSWORD`, `SEED_AGENTE_PASSWORD` | Contraseñas de los usuarios de prueba | obligatorias en producción |

## Pruebas automatizadas de seguridad (UTN-10)

```bash
pytest
```

Ese único comando ejecuta toda la suite y genera:
- `reportes/reporte-seguridad.html` (reporte HTML)
- `reportes/junit.xml` (reporte XML)

Las pruebas simulan producción: DEBUG desactivado y HTTPS. Para correrlas contra PostgreSQL, defina `DATABASE_URL`. GitHub Actions corre la suite en cada push, con PostgreSQL 16, y guarda el reporte como artefacto.

Para filtrar por categoría: `pytest -m sqli`, `-m xss`, `-m csrf`, `-m sesion`, `-m acceso`, `-m encabezados`, `-m auditoria`.

## Scripts de base de datos

- `db/01_esquema.sql`: esquema completo de PostgreSQL.
- `db/02_datos_ejemplo.sql`: permisos, roles, usuarios con contraseñas locales y datos de negocio ficticios.
- Para regenerarlos: `DATABASE_URL=postgres://.../bd_vacia bash scripts/exportar_sql.sh`.

La forma recomendada de crear la base es `python manage.py migrate && python manage.py seed`.

## Despliegue en Render

1. En Render, ir a **New → Blueprint** y seleccionar este repositorio. Render lee `render.yaml` y crea PostgreSQL (gratis) y el servicio web.
2. Definir `SEED_SUPERADMIN_PASSWORD`, `SEED_AUDITOR_PASSWORD` y `SEED_AGENTE_PASSWORD` cuando Render las pida.
3. El build (`build.sh`) instala, corre migraciones, carga el seed y ejecuta `check --deploy`.

## Requerimientos de seguridad

| ID | Dónde se implementa |
|---|---|
| UTN-01 | Django + PostgreSQL (`config/settings.py`, `render.yaml`) |
| UTN-02 | Argon2id: `cuentas/hashers.py`, validadores en `config/settings.py` |
| UTN-03 | CRUD de Vehículo: `vehiculos/` |
| UTN-04 | CRUD de usuarios: `administracion/` |
| UTN-05 / 06 | `cuentas/models.py` (Permiso, Rol), `core/permisos.py`, roles en `core/management/commands/seed.py` |
| UTN-07a | ORM de Django en todo el proyecto (sin SQL crudo) |
| UTN-07b | Autoescape, CSP, `static/js/` sin innerHTML |
| UTN-07c | `core/middleware.py` (InactividadSesionMiddleware), configuración de cookies, LoginRequiredMiddleware |
| UTN-07d | CsrfViewMiddleware, `core/views.py` (csrf_fallido) |
| UTN-08 | `config/settings.py` (SECURE_*, SECURE_CSP), `core/middleware.py` |
| UTN-09 | `core/models.py` (RegistroAuditoria), `core/auditoria.py`, `cuentas/signals.py` |
| UTN-10 | `tests/`, `pytest.ini`, `.github/workflows/pruebas.yml` |
