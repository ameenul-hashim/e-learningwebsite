#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
# Ensure collectstatic succeeds or fails the entire build
python manage.py collectstatic --no-input || { echo "Collectstatic failed"; exit 1; }
