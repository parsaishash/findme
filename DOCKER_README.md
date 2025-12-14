# Docker Setup for FindMe

This document explains how to run the FindMe Django application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd /path/to/findme
   ```

2. **Copy the environment file:**
   ```bash
   cp findme/env.example findme/.env
   ```

3. **Edit the `.env` file with your configuration:**
   - Set `DJANGO_SECRET_KEY` to a secure random string
   - Configure `FILE_SERVER_ROOT` (defaults to `./data`)
   - Set database credentials if using PostgreSQL

4. **Build and start the application:**
   ```bash
   make build
   make up
   ```

5. **Run database migrations:**
   ```bash
   make migrate
   ```

6. **Create a superuser (optional):**
   ```bash
   make createsuperuser
   ```

The application will be available at http://localhost:8000

## Development vs Production

### Development Mode (Default)
The default `docker-compose.yml` with `docker-compose.override.yml` provides:
- Hot reloading of code changes
- Django development server
- Volume mounts for source code
- Debug logging

### Production Mode
Use the base `docker-compose.yml` without overrides:
```bash
docker-compose -f docker-compose.yml up -d
```

This provides:
- Gunicorn WSGI server
- Optimized Docker images
- Production logging levels

### Simplified Development
For a simpler development setup, use `docker-compose.dev.yml`:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Available Services

- **web**: Django application (port 8000)
- **redis**: Redis cache/message broker
- **celery_worker**: Background task worker
- **celery_beat**: Scheduled task scheduler
- **db**: PostgreSQL database (optional, defaults to SQLite)

## Useful Commands

### Using Make (Recommended)
```bash
make help           # Show all available commands
make build          # Build Docker images
make up             # Start all services
make down           # Stop all services
make logs           # Show logs
make shell          # Open shell in web container
make migrate        # Run Django migrations
make test           # Run tests
```

### Using Docker Compose Directly
```bash
# Development
docker-compose build
docker-compose up -d
docker-compose logs -f web
docker-compose exec web python manage.py shell

# Production
docker-compose -f docker-compose.yml up -d --build
docker-compose -f docker-compose.yml logs -f

# Cleanup
docker-compose down -v  # Remove volumes too
docker-compose down --rmi all  # Remove images too
```

## Database Configuration

### SQLite (Default for Development)
No additional configuration needed. Database file is stored in the project root.

### PostgreSQL (Production Recommended)
1. Start PostgreSQL:
   ```bash
   docker-compose --profile postgres up -d db
   ```

2. Configure environment variables in `.env`:
   ```
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   POSTGRES_DB=findme
   POSTGRES_USER=findme
   POSTGRES_PASSWORD=your_secure_password
   ```

3. Run migrations:
   ```bash
   make migrate
   ```

## File Storage

- **Data directory**: Mounted at `./data` for file uploads
- **Static files**: Served via Nginx in production (volume: `static_volume`)
- **Media files**: User-uploaded content (volume: `media_volume`)

## Health Checks

The application includes health check endpoints:
- `/health/`: Basic Django health check
- Container health checks are configured for web, Redis, and database services

## Troubleshooting

### Common Issues

1. **Port 8000 already in use:**
   ```bash
   # Change the port in docker-compose.override.yml
   ports:
     - "8001:8000"
   ```

2. **Permission issues with data directory:**
   ```bash
   sudo chown -R $USER:$USER data/
   ```

3. **Database connection issues:**
   - Ensure PostgreSQL is running: `docker-compose ps db`
   - Check logs: `docker-compose logs db`

4. **Static files not loading:**
   ```bash
   make collectstatic
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f celery_worker

# Enter container for debugging
docker-compose exec web bash
docker-compose exec web python manage.py dbshell
```

## Environment Variables

Key environment variables (see `.env.example`):

- `DJANGO_ENV`: Environment (development/production)
- `DJANGO_DEBUG`: Enable/disable debug mode
- `DJANGO_SECRET_KEY`: Django secret key (required)
- `FILE_SERVER_ROOT`: Directory for file storage
- `CELERY_BROKER_URL`: Redis URL for Celery
- `POSTGRES_*`: PostgreSQL configuration

## Production Deployment

For production deployment:

1. Use `docker-compose.yml` (without overrides)
2. Set `DJANGO_DEBUG=0`
3. Configure proper `DJANGO_ALLOWED_HOSTS`
4. Use environment-specific `.env` files
5. Set up proper SSL/TLS termination
6. Configure backup strategies for database and volumes

## Backup and Restore

### Database Backup
```bash
make db-backup  # Creates timestamped SQL file
```

### Database Restore
```bash
make db-restore FILE=backup_20231201_120000.sql
```

### Volume Backup
```bash
docker run --rm -v findme_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```
