#!/bin/bash
set -e

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
# collectstatic will create staticfiles/ output for Vercel's @vercel/static
python manage.py collectstatic --noinput

