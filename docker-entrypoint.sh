#!/bin/sh
# Aplica migraciones pendientes antes de levantar el server. Asi "docker compose up" desde
# cero deja la DB lista sin que quien clona el repo tenga que correr alembic a mano.
set -e

echo "Aplicando migraciones..."
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
