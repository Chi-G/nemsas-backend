#!/bin/bash
set -e

# Run database migrations
if [ "$FORCE_DB_RESET" = "true" ]; then
    echo "⚠️ [$(date)] CRITICAL: FORCE_DB_RESET is set to true."
    echo "[$(date)] ☢️ DROPPING ALL EXISTING DATABASE SCHEMAS TO REBUILD FROM SCRATCH..."
    
    # Connect to postgres and recreate schema public
    # We pass variables directly from python core if configured, but simplest is using python inline
    python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def nuke():
    print('Connecting to drop schema...')
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))
    async with engine.begin() as conn:
        await conn.execute(text('DROP SCHEMA public CASCADE;'))
        await conn.execute(text('CREATE SCHEMA public;'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO public;'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO pg_database_owner;')) # required by modern pg
    await engine.dispose()
    print('✅ Schema public cleared!')

if __name__ == '__main__':
    try:
        asyncio.run(nuke())
    except Exception as e:
        print(f'Error nuking: {e}')
"
    echo "[$(date)] 🏗 Rebuilding tables from clean slate..."
else
    echo "[$(date)] 🛡 Preserving existing data. Running incremental schema upgrades..."
fi

echo "[$(date)] 🚀 Running database migrations (alembic upgrade head)..."
alembic upgrade head

# Seed base data
echo "[$(date)] 🌱 Seeding database..."
python -m scripts.seed_all

echo "[$(date)] ✨ Startup sequence complete."

echo "Starting application server..."
# Start Gunicorn
exec gunicorn app.main:app \
    --workers=3 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000 \
    --timeout=60 \
    --keep-alive=5 \
    --graceful-timeout=30 \
    --access-logfile=- \
    --error-logfile=-
