#!/bin/bash
set -e

# Wait for database if needed (though depends_on with condition should handle it)
echo "Running database migrations..."
alembic upgrade head

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
