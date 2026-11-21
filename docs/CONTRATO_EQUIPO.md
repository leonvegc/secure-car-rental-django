# Contrato técnico del equipo

**Todos deben leer este documento antes de escribir código.** Explica cómo está
armada la base y las reglas que nadie puede romper. Si algo de aquí no les
alcanza, pregunten a Cristopher antes de inventar.

## 1. Quién es dueño de qué

| Persona | Rama | Carpetas que PUEDE modificar |
|---|---|---|
| Cristopher | `feature/base-seguridad` | `config/`, `core/`, `cuentas/`, todos los `models.py` y `migrations/`, `templates/base.html`, `static/`, `tests/conftest.py`, `tests/test_seguridad_base.py`, `render.yaml`, `build.sh` |
| Josue | `feature/usuarios-roles` | `administracion/`, `templates/administracion/`, `tests/test_administracion.py`, `docs/` (sección suya y documento técnico) |
| Stephany | `feature/vehiculos-clientes` | `vehiculos/` y `clientes/` (excepto `models.py`), `templates/vehiculos/`, `templates/clientes/`, `tests/test_vehiculos.py`, `tests/test_clientes.py`, `README.md` (sección de despliegue) |
| Jeremy | `feature/alquileres` | `alquileres/` (excepto `models.py`), `templates/alquileres/`, `tests/test_alquileres.py` |

- **Nadie toca `models.py` ni crea migraciones.** Los modelos ya están completos.
  Si de verdad hace falta un campo, se le pide a Cristopher.
- `static/css/app.css`: se pueden **agregar** clases al final, sin borrar las existentes.

## 2. Estructura

```
config/        settings.py (seguridad), settings_test.py, urls.py
core/          permisos.py, auditoria.py, middleware.py, models.py (RegistroAuditoria),
               templatetags/seguridad.py, views.py (errores), management/commands/seed.py
cuentas/       Usuario, Rol, Permiso, login/logout, hash Argon2id
administracion/  (Josue) usuarios, roles, auditoría
vehiculos/     (Stephany) Vehiculo
clientes/      (Stephany) Cliente
alquileres/    (Jeremy) Alquiler
templates/     base.html, errores/, cuentas/, core/  + una carpeta por app
tests/         conftest.py (fixtures) + un archivo por módulo
```

## 3. Modelos disponibles (no modificar)

- `cuentas.Usuario`: `username`, `nombre_completo`, `identificacion`, `email`, `rol` (FK), `is_active`, `last_login`, `password` (hash). Métodos: `tiene_permiso("x.y")`, `codigos_permiso()`, propiedad `es_superadmin`. Se crea con `Usuario.objects.create_user(username, email, password, rol, nombre_completo=..., identificacion=...)`.
- `cuentas.Rol`: `nombre`, `descripcion`, `permisos` (M2M), `es_superadmin` y `es_sistema` (**no editables desde la UI, nunca ponerlos en un formulario**).
- `cuentas.Permiso`: `codigo`, `modulo`, `accion`. Es un catálogo fijo creado por el seed, **no se hace CRUD de permisos**: solo se asignan a roles.
- `core.RegistroAuditoria`: `fecha_hora`, `tipo`, `usuario`, `username`, `ip`, `ruta`, `metodo`, `detalle`. No se puede editar ni borrar.
- `vehiculos.Vehiculo`: `placa` (única, se guarda en mayúscula), `marca`, `modelo`, `categoria` (choices), `tarifa_diaria` (>0), `estado` (DISPONIBLE, ALQUILADO, MANTENIMIENTO).
- `clientes.Cliente`: `cedula` (única, 9 a 12 dígitos), `nombre_completo`, `numero_licencia`, `vencimiento_licencia`, `telefono`, `correo`. Método `licencia_vigente_hasta(fecha)`.
- `alquileres.Alquiler`: `codigo` (automático), `cliente`, `vehiculo`, `fecha_inicio`, `fecha_fin`, `dias`, `tarifa_diaria` (copia), `total`, `estado` (ACTIVO, FINALIZADO), `fecha_devolucion`, `registrado_por`, `recibido_por`. Restricciones en la BD: `fecha_fin > fecha_inicio`, `dias >= 1`, `total > 0`.

## 4. Permisos (UTN-05) y roles (UTN-06)

Código = `modulo.accion`. Módulos: `usuarios`, `roles`, `vehiculos`, `clientes`, `alquileres`, `reportes`.
Acciones: `ver`, `crear`, `editar`, `borrar`, y `ver_reportes` (solo en `reportes`).

| Rol | Permisos iniciales (seed) |
|---|---|
| SuperAdmin | `usuarios.*`, `roles.*`, `vehiculos.ver`, `reportes.ver_reportes` + auditoría (fija) |
| Auditor | `usuarios.ver`, `vehiculos.ver` |
| Agente de alquiler | `usuarios.ver`, `vehiculos.*`, `clientes.*`, `alquileres.*`, `reportes.ver_reportes` |

- La **auditoría** y la **gestión de roles** exigen además ser SuperAdmin (`@solo_superadmin`): ningún otro rol puede llegar ahí aunque le asignen el permiso.
- El Auditor **no** ve clientes ni alquileres (dato sensible).

## 5. Cómo proteger una vista (OBLIGATORIO en todas)

```python
from core.permisos import requiere_permiso, solo_superadmin, PermisoRequeridoMixin

@requiere_permiso("vehiculos.crear")
def crear(request): ...

class VehiculoCrear(PermisoRequeridoMixin, CreateView):
    permiso_requerido = "vehiculos.crear"
```

- Sin permiso → `PermissionDenied` → **HTTP 403** con página genérica, y queda en la auditoría **automáticamente**. No escriban su propio 403.
- Las vistas que modifican datos aceptan **solo POST**: `@require_POST`, o `@require_http_methods(["GET", "POST"])` para formularios. **Borrar siempre por POST** con formulario y `{% csrf_token %}`, nunca con un enlace GET.
- Todas las rutas exigen sesión automáticamente (LoginRequiredMiddleware). **No usen `@login_not_required`.**
- Para objetos por ID usen `get_object_or_404(Modelo, pk=pk)` **después** de verificar el permiso.

## 6. Auditoría (UTN-09)

```python
from core.auditoria import registrar_evento
from core.models import RegistroAuditoria
registrar_evento(request, RegistroAuditoria.Tipo.CAMBIO_ROL, detalle=f"{u.username}: {antes} -> {despues}")
```

Ya se registran solos: login exitoso y fallido, bloqueo, logout, sesión expirada, 403 y CSRF rechazado.
Josue registra los cambios de rol y de permisos. Stephany y Jeremy usan `Tipo.OPERACION` para crear, editar, borrar y devolver.
**En `detalle` nunca escriban contraseñas ni el número de licencia completo.**

## 7. Reglas de seguridad que NADIE puede romper

1. **SQL Injection (UTN-07a):** solo ORM (`filter`, `Q`, `annotate`). **Prohibido** `raw()`, `extra()`, `cursor.execute()`, f-strings o `%` con SQL.
2. **XSS (UTN-07b):** nunca `|safe`, `mark_safe`, `{% autoescape off %}`, ni `format_html` con datos sin escapar. En JS nunca `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` ni `eval`: usen `textContent`.
3. **CSP:** no hay `<script>` en línea, ni `onclick=`, ni `style="..."`. El JS va en `static/js/*.js` y los estilos en `static/css/app.css`. Lo en línea **no funciona**: la CSP lo bloquea.
4. **CSRF (UTN-07d):** todo `<form method="post">` lleva `{% csrf_token %}`. Nunca `@csrf_exempt`.
5. **Formularios:** `ModelForm` con `fields = [...]` **explícito** (nunca `"__all__"` ni `exclude`), para evitar asignación masiva. Validen y limpien en `clean_<campo>()` (`strip()`, mayúsculas, rangos).
6. **Búsquedas y filtros por GET:** validen con un `forms.Form` (`max_length`, choices) antes de usarlos en el ORM.
7. **Datos sensibles:** la licencia se muestra **enmascarada** en listados (`{{ c.numero_licencia|enmascarar }}` con `{% load seguridad %}`). Nada sensible va en URLs ni en mensajes.
8. **Errores:** nunca muestren excepciones al usuario. Usen `messages.error(request, "texto genérico")`. Capturen `ProtectedError` e `IntegrityError` con un mensaje amable.
9. **Nada de secretos** en el código: todo por variables de entorno.
10. **No desactiven** nada de `config/settings.py`. Si algo choca, avisen.

## 8. Plantillas

- Extiendan `base.html` y usen `{% block titulo %}` y `{% block contenido %}`.
- Para mostrar u ocultar botones según el permiso:
  `{% load seguridad %}{% if permisos_usuario|tiene:"vehiculos.borrar" %}...{% endif %}`.
  Ocultar el botón **no reemplaza** proteger la vista: las dos cosas son obligatorias.
- CSS: Pico.css ya cargado. Formularios: `<form method="post">{% csrf_token %}{{ form.as_div }}<button>Guardar</button></form>`.
- Acciones en tablas: `<td class="tabla-acciones">…</td>`.

## 9. Pruebas (UTN-10)

- Un solo comando: `pytest`, que genera `reportes/reporte-seguridad.html` y `reportes/junit.xml`.
- Fixtures listas en `tests/conftest.py`: `cliente_superadmin`, `cliente_auditor`, `cliente_agente`, `cliente_anonimo`, `cliente_csrf`, `login_csrf(usuario)`, `superadmin`, `auditor`, `agente`, y las listas de ataques `PAYLOADS_SQLI` y `PAYLOADS_XSS`.
- Cada persona escribe **mínimo 4 pruebas** de su módulo:
  - 1 de SQL Injection.
  - 1 de XSS almacenado (guardar el payload y verificar que sale escapado).
  - 1 de 403 (un rol sin permiso intenta la acción por POST directo).
  - 1 de CSRF o de regla de negocio.
- Marquen cada prueba con `@pytest.mark.sqli`, `xss`, `acceso`, `csrf` o `negocio`, y pongan un docstring que diga qué caso cubre (TC-xx).
- `pytest` debe pasar **completo** antes de abrir el Pull Request.

## 10. Git

- Trabajen **solo en su rama**: `git checkout -b feature/<su-rama>` desde `main` actualizado.
- Hagan **commits pequeños y frecuentes**, con mensajes en español: `feat(vehiculos): CRUD con validación de placa`, `test(alquileres): RN-9.1 licencia vencida`, `fix: ...`, `docs: ...`.
- Antes del PR: `git pull origin main`, corran `pytest`, y después `git push` y abran el Pull Request a `main`. Cristopher revisa y hace el merge.
- Nunca suban `.env`, `db.sqlite3` ni `reportes/`.
- Cada integrante debe tener commits propios: es evidencia de participación y se evalúa.
