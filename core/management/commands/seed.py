"""
Carga los datos iniciales: permisos, roles, usuarios de prueba y datos de ejemplo.

    python manage.py seed            # idempotente: no duplica ni sobreescribe
    python manage.py seed --sin-ejemplos

Las contraseñas de los usuarios de prueba se leen de variables de entorno:
SEED_SUPERADMIN_PASSWORD, SEED_AUDITOR_PASSWORD, SEED_AGENTE_PASSWORD.
En desarrollo (DEBUG=1) hay valores por defecto; en producción son obligatorias.
Todos los datos son FICTICIOS.
"""

import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from alquileres.models import Alquiler
from clientes.models import Cliente
from cuentas.models import Permiso, Rol, Usuario
from vehiculos.models import Vehiculo

A = Permiso.Accion
M = Permiso.Modulo
CRUD = [A.VER, A.CREAR, A.EDITAR, A.BORRAR]

CATALOGO_PERMISOS = (
    [(M.USUARIOS, a) for a in CRUD]
    + [(M.ROLES, a) for a in CRUD]
    + [(M.VEHICULOS, a) for a in CRUD]
    + [(M.CLIENTES, a) for a in CRUD]
    + [(M.ALQUILERES, a) for a in CRUD]
    + [(M.REPORTES, A.VER_REPORTES)]
)

ROLES = {
    "SuperAdmin": {
        "descripcion": "CRUD de usuarios y roles, asigna permisos, ve reportes y auditoría.",
        "es_superadmin": True,
        "permisos": [f"usuarios.{a}" for a in CRUD]
        + [f"roles.{a}" for a in CRUD]
        + ["vehiculos.ver", "reportes.ver_reportes"],
    },
    "Auditor": {
        "descripcion": "Solo lectura de usuarios y de vehículos.",
        "es_superadmin": False,
        "permisos": ["usuarios.ver", "vehiculos.ver"],
    },
    "Agente de alquiler": {
        "descripcion": "CRUD de vehículos, clientes y alquileres; reportes; solo lectura de usuarios.",
        "es_superadmin": False,
        "permisos": ["usuarios.ver"]
        + [f"vehiculos.{a}" for a in CRUD]
        + [f"clientes.{a}" for a in CRUD]
        + [f"alquileres.{a}" for a in CRUD]
        + ["reportes.ver_reportes"],
    },
}

USUARIOS = [
    # username, nombre, identificación, correo, rol, variable de entorno, clave de desarrollo
    ("superadmin", "Sofía Administradora", "100000001", "superadmin@alquiler.test", "SuperAdmin",
     "SEED_SUPERADMIN_PASSWORD", "Super#Admin2026!"),
    ("auditor", "Andrés Auditor", "100000002", "auditor@alquiler.test", "Auditor",
     "SEED_AUDITOR_PASSWORD", "Audit#Lectura2026!"),
    ("agente", "Gabriela Agente", "100000003", "agente@alquiler.test", "Agente de alquiler",
     "SEED_AGENTE_PASSWORD", "Agente#Alquila2026!"),
]


class Command(BaseCommand):
    help = "Carga permisos, roles, usuarios de prueba y datos de ejemplo (ficticios)."

    def add_arguments(self, parser):
        parser.add_argument("--sin-ejemplos", action="store_true", help="Solo seguridad, sin datos de negocio")

    @transaction.atomic
    def handle(self, *args, **opts):
        permisos = {}
        for modulo, accion in CATALOGO_PERMISOS:
            p, _ = Permiso.objects.get_or_create(
                modulo=modulo,
                accion=accion,
                defaults={"descripcion": f"{M(modulo).label}: {A(accion).label}"},
            )
            permisos[p.codigo] = p

        for nombre, datos in ROLES.items():
            rol, creado = Rol.objects.get_or_create(nombre=nombre, defaults={"descripcion": datos["descripcion"]})
            # Los roles base son de sistema (no se pueden borrar desde la UI).
            Rol.objects.filter(pk=rol.pk).update(es_superadmin=datos["es_superadmin"], es_sistema=True)
            if creado:
                rol.permisos.set([permisos[c] for c in datos["permisos"]])

        for username, nombre, ident, correo, rol, var, clave_dev in USUARIOS:
            if Usuario.objects.filter(username=username).exists():
                continue
            clave = os.environ.get(var) or (clave_dev if settings.DEBUG else None)
            if not clave:
                raise CommandError(f"Defina la variable de entorno {var} para crear '{username}'.")
            Usuario.objects.create_user(
                username=username,
                email=correo,
                password=clave,
                rol=Rol.objects.get(nombre=rol),
                nombre_completo=nombre,
                identificacion=ident,
            )
            self.stdout.write(f"Usuario creado: {username} ({rol})")

        if not opts["sin_ejemplos"]:
            self._datos_ejemplo()
        self.stdout.write(self.style.SUCCESS("Seed completado."))

    def _datos_ejemplo(self):
        if Vehiculo.objects.exists():
            return
        V = Vehiculo.Categoria
        vehiculos = [
            ("BCD-123", "Toyota", "Yaris", V.ECONOMICO, "25000"),
            ("BCD-456", "Hyundai", "Accent", V.SEDAN, "30000"),
            ("CRS-789", "Toyota", "RAV4", V.SUV, "45000"),
            ("TRK-321", "Nissan", "Frontier", V.PICKUP, "50000"),
            ("MBS-654", "Hyundai", "H1", V.MICROBUS, "65000"),
        ]
        objs = {}
        for placa, marca, modelo, cat, tarifa in vehiculos:
            objs[placa] = Vehiculo.objects.create(
                placa=placa, marca=marca, modelo=modelo, categoria=cat, tarifa_diaria=Decimal(tarifa)
            )
        objs["TRK-321"].estado = Vehiculo.Estado.MANTENIMIENTO
        objs["TRK-321"].save()

        hoy = timezone.localdate()
        c1 = Cliente.objects.create(
            cedula="200000001", nombre_completo="Laura Pérez Ficticia", numero_licencia="LIC-0001",
            vencimiento_licencia=hoy + timedelta(days=700), telefono="88880001", correo="laura@cliente.test",
        )
        Cliente.objects.create(
            cedula="200000002", nombre_completo="Mario Rojas Ficticio", numero_licencia="LIC-0002",
            vencimiento_licencia=hoy - timedelta(days=30), telefono="88880002", correo="mario@cliente.test",
        )  # licencia vencida: sirve para probar RN-9.1
        Cliente.objects.create(
            cedula="200000003", nombre_completo="Ana Mora Ficticia", numero_licencia="LIC-0003",
            vencimiento_licencia=hoy + timedelta(days=365),
        )

        agente = Usuario.objects.filter(username="agente").first()
        v = objs["CRS-789"]
        inicio, fin = hoy - timedelta(days=10), hoy - timedelta(days=7)
        Alquiler.objects.create(
            cliente=c1, vehiculo=v, fecha_inicio=inicio, fecha_fin=fin, dias=3,
            tarifa_diaria=v.tarifa_diaria, total=v.tarifa_diaria * 3,
            estado=Alquiler.Estado.FINALIZADO, fecha_devolucion=timezone.now() - timedelta(days=7),
            registrado_por=agente, recibido_por=agente,
        )
        self.stdout.write("Datos de ejemplo creados (vehículos, clientes y un alquiler finalizado).")
