#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations FIRST (creates database tables)
python manage.py migrate

# Create superuser AFTER migrations (tables must exist)
python create_superuser.py

# Collect static files
python manage.py collectstatic --noinput

# Ensure cache directory exists
mkdir -p django_cache
