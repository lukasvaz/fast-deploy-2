#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Run makemigrations
echo "Running makemigrations..."
python manage.py makemigrations

# Run migrate
echo "Running migrate..."
python manage.py migrate

echo "Migrations completed successfully."