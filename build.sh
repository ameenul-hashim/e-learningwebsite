#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
# We run this during build to ensure static assets are ready
python manage.py collectstatic --no-input
