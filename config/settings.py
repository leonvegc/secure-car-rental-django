"""
Configuración de Django para el sistema de Alquiler de Vehículos (ISW-622).

Toda la configuración sensible se lee de variables de entorno (ver .env.example).
Los valores por defecto son SEGUROS: si no se define DEBUG, el sistema arranca
en modo producción (DEBUG=False, HTTPS obligatorio, cookies Secure).
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(nombre, defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def env_list(nombre, defecto=""):
    return [v.strip() for v in os.environ.get(nombre, defecto).split(",") if v.strip()]


# ---------------------------------------------------------------------------
# Núcleo
# ---------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "solo-desarrollo-local-no-usar-en-produccion-" + "x" * 20
    else:
        raise ImproperlyConfigured("Defina la variable de entorno SECRET_KEY.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Render publica el nombre del host en esta variable.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

INSTALLED_APPS = [
    # Django (sin django.contrib.admin: no se expone panel /admin/)
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "axes",
    # Propias
    "core",
    "cuentas",
    "administracion",
    "vehiculos",
    "clientes",
    "alquileres",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # UTN-07c: cierra la sesión tras SESION_INACTIVIDAD_SEGUNDOS sin actividad.
    "core.middleware.InactividadSesionMiddleware",
    # UTN-07c: ninguna ruta es accesible sin sesión válida (salvo @login_not_required).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # UTN-08: Content-Security-Policy nativo de Django 6.
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    # UTN-08: encabezados adicionales y no-cache para páginas autenticadas.
    "core.middleware.EncabezadosSeguridadMiddleware",
    # Protección contra fuerza bruta (debe ir de último).
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            # Escape automático activado (valor por defecto). NUNCA desactivarlo.
            "autoescape": True,
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.seguridad",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos (UTN-01): PostgreSQL mediante DATABASE_URL.
# Sin DATABASE_URL se usa SQLite SOLO para desarrollo local y pruebas.
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
            ssl_require=env_bool("DB_SSL_REQUIRE", not DEBUG),
        )
    }
elif DEBUG or env_bool("PERMITIR_SQLITE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured("Defina DATABASE_URL (PostgreSQL) en producción.")

# ---------------------------------------------------------------------------
# Autenticación y contraseñas (UTN-02)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "cuentas.Usuario"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # bloqueo por fuerza bruta
    "django.contrib.auth.backends.ModelBackend",
]

# Argon2id (UTN-02). Ver cuentas/hashers.py para los parámetros.
PASSWORD_HASHERS = [
    "cuentas.hashers.Argon2idHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "cuentas.validators.ComplejidadValidator"},
]

LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "core:inicio"
LOGOUT_REDIRECT_URL = "cuentas:login"

# ---------------------------------------------------------------------------
# Sesión (UTN-07c)
# ---------------------------------------------------------------------------
SESION_INACTIVIDAD_SEGUNDOS = int(os.environ.get("SESION_INACTIVIDAD_SEGUNDOS", "60"))
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # la cookie solo lleva un ID aleatorio
SESSION_COOKIE_NAME = "sid"  # nombre genérico, no revela el framework
# El corte exacto a los 60 s lo hace core.middleware.InactividadSesionMiddleware
# (y lo registra en la auditoría). La sesión en BD vence unos segundos después
# como segunda barrera.
SESSION_COOKIE_AGE = SESION_INACTIVIDAD_SEGUNDOS + 5
SESSION_SAVE_EVERY_REQUEST = True  # cada solicitud renueva la ventana de 60 s
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"

# ---------------------------------------------------------------------------
# CSRF (UTN-07d)
# ---------------------------------------------------------------------------
CSRF_COOKIE_NAME = "csrft"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_FAILURE_VIEW = "core.views.csrf_fallido"

# ---------------------------------------------------------------------------
# HTTPS y encabezados (UTN-08)
# ---------------------------------------------------------------------------
USAR_HTTPS = env_bool("USAR_HTTPS", not DEBUG)
SESSION_COOKIE_SECURE = USAR_HTTPS
CSRF_COOKIE_SECURE = USAR_HTTPS
SECURE_SSL_REDIRECT = USAR_HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Render termina TLS
SECURE_HSTS_SECONDS = 31536000 if USAR_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USAR_HTTPS
SECURE_HSTS_PRELOAD = False  # un subdominio de onrender.com no puede entrar a la lista preload
SILENCED_SYSTEM_CHECKS = ["security.W021"]
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# CSP estricta: sin scripts ni estilos en línea, sin recursos externos.
SECURE_CSP = {
    "default-src": [CSP.NONE],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "base-uri": [CSP.NONE],
    "object-src": [CSP.NONE],
}
if USAR_HTTPS:
    SECURE_CSP["upgrade-insecure-requests"] = True

# Número de proxies de confianza delante de la app (Render = 1). Se usa para
# obtener la IP real del cliente desde X-Forwarded-For sin aceptar IPs falsas.
TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", "1"))
# Encabezado confiable con la IP del cliente puesto por el proxy de borde.
# En Render: "True-Client-IP" (lo agrega Cloudflare; Render no limpia X-Forwarded-For).
CLIENT_IP_HEADER = os.environ.get("CLIENT_IP_HEADER", "")

# ---------------------------------------------------------------------------
# Protección contra fuerza bruta (django-axes)
# ---------------------------------------------------------------------------
AXES_FAILURE_LIMIT = int(os.environ.get("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = timedelta(minutes=int(os.environ.get("AXES_COOLOFF_MINUTOS", "15")))
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "core.utils.obtener_ip_axes"
AXES_LOCKOUT_TEMPLATE = "cuentas/bloqueado.html"
AXES_ENABLE_ADMIN = False
AXES_VERBOSE = False
AXES_SENSITIVE_PARAMETERS = ["password"]

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Costa_Rica"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos (servidos por WhiteNoise, mismo origen => CSP 'self')
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Límites de carga para evitar abuso de formularios.
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# ---------------------------------------------------------------------------
# Registro (logs) sin datos sensibles
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
WHITENOISE_ALLOW_ALL_ORIGINS = False  # no enviar Access-Control-Allow-Origin: *
