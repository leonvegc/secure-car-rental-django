"""
Modelos de seguridad: Permiso, Rol y Usuario (UTN-02, UTN-04, UTN-05, UTN-06).

- Los permisos se asignan a ROLES, nunca a usuarios (no se usa PermissionsMixin).
- Un permiso es la combinación módulo + acción, por ejemplo "vehiculos.crear".
- El rol SuperAdmin se identifica con es_superadmin=True (no editable desde la UI).
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from .validators import validar_identificacion, validar_texto_nombre, validar_username


class Permiso(models.Model):
    class Accion(models.TextChoices):
        VER = "ver", "Ver"
        CREAR = "crear", "Crear"
        EDITAR = "editar", "Editar"
        BORRAR = "borrar", "Borrar"
        VER_REPORTES = "ver_reportes", "Ver reportes"

    class Modulo(models.TextChoices):
        USUARIOS = "usuarios", "Usuarios"
        ROLES = "roles", "Roles"
        VEHICULOS = "vehiculos", "Vehículos"
        CLIENTES = "clientes", "Clientes"
        ALQUILERES = "alquileres", "Alquileres"
        REPORTES = "reportes", "Reportes"

    codigo = models.CharField(max_length=50, unique=True, editable=False)
    modulo = models.CharField(max_length=20, choices=Modulo.choices)
    accion = models.CharField(max_length=20, choices=Accion.choices)
    descripcion = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["modulo", "accion"]
        constraints = [
            models.UniqueConstraint(fields=["modulo", "accion"], name="permiso_modulo_accion_unico"),
        ]

    def save(self, *args, **kwargs):
        self.codigo = f"{self.modulo}.{self.accion}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_modulo_display()} - {self.get_accion_display()}"


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True, validators=[validar_texto_nombre])
    descripcion = models.CharField(max_length=200, blank=True)
    permisos = models.ManyToManyField(Permiso, related_name="roles", blank=True)
    # Solo el seed puede marcar estos campos; los formularios NUNCA deben exponerlos.
    es_superadmin = models.BooleanField(default=False, editable=False)
    es_sistema = models.BooleanField(default=False, editable=False)  # no se puede borrar
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, password, rol, **extra):
        if not username:
            raise ValueError("El username es obligatorio")
        usuario = self.model(
            username=username, email=self.normalize_email(email).lower(), rol=rol, **extra
        )
        usuario.set_password(password)
        usuario.full_clean(exclude=["password"])
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, email, password, **extra):
        rol = Rol.objects.get(es_superadmin=True)
        return self.create_user(username, email, password, rol=rol, **extra)


class Usuario(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True, validators=[validar_username])
    nombre_completo = models.CharField(max_length=100, validators=[validar_texto_nombre])
    identificacion = models.CharField(max_length=12, unique=True, validators=[validar_identificacion])
    email = models.EmailField(max_length=254, unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name="usuarios")
    is_active = models.BooleanField("activo", default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    # last_login (último inicio de sesión) y password (hash) vienen de AbstractBaseUser.

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email", "nombre_completo", "identificacion"]

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username

    # ---- Autorización -----------------------------------------------------
    @property
    def es_superadmin(self):
        return bool(self.is_active and self.rol_id and self.rol.es_superadmin)

    def codigos_permiso(self):
        """Conjunto de códigos de permiso del rol (cacheado por instancia/solicitud)."""
        if not self.is_active or not self.rol_id:
            return frozenset()
        if not hasattr(self, "_cache_permisos"):
            self._cache_permisos = frozenset(self.rol.permisos.values_list("codigo", flat=True))
        return self._cache_permisos

    def tiene_permiso(self, codigo):
        return codigo in self.codigos_permiso()

    # Django pide estos métodos a veces (p. ej. plantillas de auth); se niegan por defecto.
    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False
