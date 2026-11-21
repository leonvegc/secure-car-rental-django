#!/usr/bin/env bash
# Regenera db/01_esquema.sql y db/02_datos_ejemplo.sql a partir de las migraciones.
# Requiere una base PostgreSQL VACÍA indicada en DATABASE_URL, y pg_dump instalado.
#   DATABASE_URL=postgres://usuario:clave@localhost:5432/alquiler_export bash scripts/exportar_sql.sh
set -o errexit
export DEBUG=1 DB_SSL_REQUIRE=0
python manage.py migrate --no-input
python manage.py seed
pg_dump --schema-only --no-owner --no-privileges "$DATABASE_URL" > db/01_esquema.sql
pg_dump --data-only --no-owner --no-privileges --column-inserts \
  --exclude-table=django_session --exclude-table='axes_*' --exclude-table=core_registroauditoria \
  "$DATABASE_URL" > db/02_datos_ejemplo.sql
echo "Listo: db/01_esquema.sql y db/02_datos_ejemplo.sql"
