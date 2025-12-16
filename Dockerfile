FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies and PostgreSQL client tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy only requirements first, then install dependencies
COPY findme/requirements.txt /app/requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy the Django application
COPY findme/ /app/

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create dedicated user and data directory
RUN addgroup --system findme && adduser --system --ingroup findme --home /app findme \
    && mkdir -p /data \
    && chown -R findme:findme /data /app

USER findme

ENV FILE_SERVER_ROOT=/data \
    DJANGO_SETTINGS_MODULE=findme.settings

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "findme.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
