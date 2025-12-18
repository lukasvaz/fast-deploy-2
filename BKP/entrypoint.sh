#!/bin/sh
# Entrypoint para desarrollo - Repositorio Académicos DCC

set -e

echo "🔍 Esperando PostgreSQL..."
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
      sleep 0.1
    done
    echo "✅ PostgreSQL iniciado"
elif [ "$DATABASE" = "postgres" ] && [ -n "$SQL_HOST" ] && [ -n "$SQL_PORT" ]; then
    while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
      sleep 0.1
    done
    echo "✅ PostgreSQL iniciado"
else
    echo "⚠️  Variables de DB no definidas, omitiendo espera"
fi

echo "🛠  Ejecutando migraciones..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# echo "📦 (Opcional) Cargando fixtures..."
echo "📦 Cargando fixtures (si existen)..."
python manage.py loaddata ./universidad/fixtures/universidad_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  universidad fixtures no encontrados"
python manage.py loaddata ./users/fixtures/users_fixture_17_11_2025.json 2>/dev/null || echo "  ⚠️  users fixtures no encontrados"
python manage.py loaddata ./persona/fixtures/persona_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  persona fixtures no encontrados"
python manage.py loaddata ./grados/fixtures/grados_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  grados fixtures no encontrados"

echo "📊 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput 2>/dev/null || echo "  ⚠️  Error al recolectar estáticos (continuando...)"

echo "🚀 Iniciando aplicación Django"
exec "$@"
