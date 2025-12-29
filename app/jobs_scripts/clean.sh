#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Flush the database (delete all data)
echo "Flushing the database..."
python manage.py flush --noinput

# Load initial data fixtures
echo "Loading data fixtures..."
python manage.py loaddata _fixtures/users/fixtures/users_fixture_23_12_2025.json
python manage.py loaddata _fixtures/universidad/fixtures/universidad_fixture_23_12_2025.json
python manage.py loaddata _fixtures/persona/fixtures/persona_fixture_23_12_2025.json
python manage.py loaddata _fixtures/grados/fixtures/grados_fixture_23_12_2025.json

echo "Database cleaned and data loaded successfully."