# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2 and other requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using pip (since uv might not be available in container)
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Fix potential line ending issues and ensure start.sh is executable
RUN ls -la scripts/start.sh && \
    python3 -c "import os; f='scripts/start.sh'; c=open(f,'rb').read().replace(b'\r\n',b'\n'); open(f,'wb').write(c)" && \
    chmod +x scripts/start.sh && \
    chown appuser:appuser scripts/start.sh

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run migrations, seed, and then start the server via start script
CMD ["/bin/bash", "scripts/start.sh"]