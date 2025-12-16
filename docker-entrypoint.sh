#!/bin/bash
set -e

# Fix permissions for mounted data directory if running as root
# This allows the container to write to host-mounted volumes
if [ "$(id -u)" = "0" ]; then
    if [ -d "/app/data" ]; then
        echo "Fixing permissions for /app/data directory..."
        chown -R findme:findme /app/data 2>/dev/null || true
        # Ensure the directory is writable
        chmod -R 755 /app/data 2>/dev/null || true
    fi
    
    # Switch to findme user and re-execute this script
    echo "Switching to findme user..."
    exec su-exec findme /bin/bash "$0" "$@"
fi

# Wait for PostgreSQL to be ready
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_DB" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up - executing command"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (idempotent operation)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute the main command
exec "$@"

