#!/usr/bin/env bash
# Comando de build de Render (ver render.yaml).
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed
python manage.py check --deploy --fail-level WARNING
