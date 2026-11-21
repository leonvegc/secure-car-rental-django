# Configuración de Gunicorn (Render la carga automáticamente desde la raíz).
import os

import gunicorn

# No revelar el servidor ni su versión en el encabezado "Server".
gunicorn.SERVER = "web"

bind = "0.0.0.0:" + os.environ.get("PORT", "10000")
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
timeout = 60
accesslog = "-"
# Límites contra solicitudes abusivas
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
