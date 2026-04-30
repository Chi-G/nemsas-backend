#!/bin/bash
set -e

# Run database migrations
echo "[$(date)] 🚀 Running database migrations..."
alembic upgrade head

# Seed base data (idempotent)
echo "[$(date)] 🌱 Seeding database (this may take a minute)..."
python -m scripts.seed

echo "[$(date)] ✨ Startup sequence complete. Starting Gunicorn..."

echo "Starting application server..."
# Start Gunicorn
exec gunicorn src.main:app \
    --workers=3 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000 \
    --timeout=60 \
    --keep-alive=5 \
    --graceful-timeout=30 \
    --access-logfile=- \
    --error-logfile=-
