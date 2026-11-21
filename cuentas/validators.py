import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class ComplejidadValidator:
    """Exige mayúscula, minúscula, número y símbolo en la contraseña."""

    reglas = [
        (r"[A-Z]", "una letra mayúscula"),
        (r"[a-z]", "una letra minúscula"),
        (r"[0-9]", "un número"),
        (r"[^A-Za-z0-9]", "un símbolo"),
    ]

    def validate(self, password, user=None):
        faltantes = [texto for patron, texto in self.reglas if not re.search(patron, password)]
        if faltantes:
            raise ValidationError(
                "La contraseña debe contener al menos " + ", ".join(faltantes) + ".",
                code="password_complejidad",
            )

    def get_help_text(self):
        return "Debe incluir mayúscula, minúscula, número y símbolo."


validar_username = RegexValidator(
    r"^[a-zA-Z0-9._-]{3,30}$",
    "Use de 3 a 30 caracteres: letras, números, punto, guion o guion bajo.",
)

validar_identificacion = RegexValidator(
    r"^[0-9]{9,12}$",
    "La identificación debe tener de 9 a 12 dígitos, sin guiones ni espacios.",
)

validar_texto_nombre = RegexValidator(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{2,100}$",
    "Solo se permiten letras, espacios, apóstrofo, punto y guion.",
)
