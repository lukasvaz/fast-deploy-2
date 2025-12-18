#!/bin/sh
# Entrypoint para producción - Repositorio Académicos DCC

set -e

echo "🔍 Esperando PostgreSQL..."
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
    while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
      sleep 0.1
    done
    echo "✅ PostgreSQL iniciado"
elif [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
      sleep 0.1
    done
    echo "✅ PostgreSQL iniciado"
else
    echo "⚠️  Variables de DB no definidas, omitiendo espera"
fi

echo "🛠  Ejecutando migraciones..."
python manage.py migrate --noinput

echo "🚀 Iniciando aplicación en modo producción"
exec "$@"