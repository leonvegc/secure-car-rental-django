"""
Uso en plantillas:
    {% load seguridad %}
    {% if permisos_usuario|tiene:"vehiculos.crear" %} ... {% endif %}
    {{ cliente.numero_licencia|enmascarar }}   ->  ******1234
"""

from django import template

register = template.Library()


@register.filter
def tiene(permisos, codigo):
    return codigo in (permisos or ())


@register.filter
def enmascarar(valor, visibles=4):
    texto = "" if valor is None else str(valor)
    visibles = int(visibles)
    if len(texto) <= visibles:
        return "*" * len(texto)
    return "*" * (len(texto) - visibles) + texto[-visibles:]
