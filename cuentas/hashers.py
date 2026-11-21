"""
UTN-02: Hash de contraseñas con Argon2id.

Django ya usa la variante Argon2id. Se ajustan los parámetros por encima del
mínimo recomendado por OWASP (m=19 MiB, t=2, p=1) sin agotar la memoria del
plan gratuito de Render (512 MB).
"""

from django.contrib.auth.hashers import Argon2PasswordHasher


class Argon2idHasher(Argon2PasswordHasher):
    algorithm = "argon2"  # mantiene el prefijo estándar "argon2$argon2id$..."
    time_cost = 3
    memory_cost = 65536  # 64 MiB
    parallelism = 2
