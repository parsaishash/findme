#!/bin/bash
set -e

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

