"""
Configuración para la suite de pruebas (UTN-10).

Simula PRODUCCIÓN: DEBUG=False y HTTPS activo (cookies Secure, HSTS), para que
las pruebas verifiquen la misma configuración que se publica en Render.
Usa PostgreSQL si DATABASE_URL está definida; si no, SQLite.
"""

import os

os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-automatizadas-0123456789abcdef")
os.environ.setdefault("PERMITIR_SQLITE", "1")
os.environ.setdefault("USAR_HTTPS", "1")
os.environ["DEBUG"] = "0"
os.environ.setdefault("SEED_SUPERADMIN_PASSWORD", "Prueba#Super2026!")
os.environ.setdefault("SEED_AUDITOR_PASSWORD", "Prueba#Audit2026!")
os.environ.setdefault("SEED_AGENTE_PASSWORD", "Prueba#Agente2026!")

from .settings import *  # noqa: E402,F401,F403

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
