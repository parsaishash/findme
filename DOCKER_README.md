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

## Environment Profiles

The `docker-compose.yml` file uses profiles to manage different environments:

### Development Mode (Default)
```bash
docker-compose --profile dev up -d
# or
make up
```

This provides:
- Hot reloading of code changes (source code mounted)
- Django development server (`runserver`)
- Volume mounts for source code
- Debug logging
- Services: `web-dev`, `celery_worker-dev`, `celery_beat-dev`, `redis`
- No database (uses SQLite by default)

### Production Mode
```bash
docker-compose --profile production --profile traefik up -d
# or
make up-prod
```

This provides:
- Gunicorn WSGI server
- Optimized Docker images
- Production logging levels
- Traefik reverse proxy
- Services: `web`, `celery_worker`, `celery_beat`, `redis`, `db`, `traefik`

### Staging Mode
```bash
docker-compose --profile staging --profile traefik up -d
```

Similar to production but with staging-specific environment variables.

### PostgreSQL Database
To use PostgreSQL instead of SQLite:
```bash
docker-compose --profile dev --profile postgres up -d db
# or for production
docker-compose --profile production --profile postgres up -d
```

## Available Services

- **web** / **web-dev**: Django application (port 8000)
- **redis**: Redis cache/message broker (internal only, no exposed ports)
- **celery_worker** / **celery_worker-dev**: Background task worker (internal only)
- **celery_beat** / **celery_beat-dev**: Scheduled task scheduler (internal only)
- **db**: PostgreSQL database (internal only, no exposed ports)
- **traefik**: Reverse proxy (ports 80, 443, 8081)

## Port Bindings

- **8000:8000** - Django web application (web/web-dev)
- **80** - HTTP entrypoint (traefik)
- **443** - HTTPS entrypoint (traefik)
- **8081** - Traefik dashboard (traefik)
- **No exposed ports** - redis, db, celery services (internal only)

## Networking

- **default**: Bridge network for internal service communication
- **traefik-net**: Bridge network for Traefik integration (used by web and traefik services)

## Useful Commands

### Using Make (Recommended)
```bash
make help           # Show all available commands
make build          # Build Docker images (dev profile)
make build-prod     # Build production images
make up             # Start all services (dev profile)
make up-prod        # Start production services
make down           # Stop all services
make logs           # Show logs
make logs-web       # Show web service logs
make logs-worker    # Show celery worker logs
make shell          # Open shell in web container
make migrate        # Run Django migrations
make test           # Run tests
```

### Using Docker Compose Directly
```bash
# Development
docker-compose --profile dev build
docker-compose --profile dev up -d
docker-compose --profile dev logs -f web-dev

# Production
docker-compose --profile production --profile traefik up -d --build
docker-compose --profile production logs -f

# Staging
docker-compose --profile staging --profile traefik up -d --build

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
   docker-compose --profile production --profile postgres up -d db
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

- **Data directory**: Mounted at `./findme/data` for file uploads
- **Static files**: Served via volume `static_volume`
- **Media files**: User-uploaded content (volume: `media_volume`)

## Health Checks

The application includes health check endpoints:
- `/health/`: Basic Django health check
- Container health checks are configured for web, Redis, and database services

## Troubleshooting

### Common Issues

1. **Port 8000 already in use:**
   Edit `docker-compose.yml` and change the port mapping:
   ```yaml
   ports:
     - "8001:8000"
   ```

2. **Permission issues with data directory:**
   ```bash
   sudo chown -R $USER:$USER findme/data/
   ```

3. **Database connection issues:**
   - Ensure PostgreSQL is running: `docker-compose ps db`
   - Check logs: `docker-compose logs db`

4. **Static files not loading:**
   ```bash
   make collectstatic
   ```

5. **Traefik network not found:**
   The `traefik-net` network is created automatically. If you see errors, ensure you're using the `traefik` profile:
   ```bash
   docker-compose --profile production --profile traefik up -d
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web-dev
docker-compose logs -f celery_worker-dev

# Enter container for debugging
docker-compose exec web-dev bash
docker-compose exec web-dev python manage.py dbshell
```

## Environment Variables

Key environment variables (see `.env.example`):

- `DJANGO_ENV`: Environment (development/production/staging)
- `DJANGO_DEBUG`: Enable/disable debug mode
- `DJANGO_SECRET_KEY`: Django secret key (required)
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `FILE_SERVER_ROOT`: Directory for file storage
- `CELERY_BROKER_URL`: Redis URL for Celery
- `POSTGRES_*`: PostgreSQL configuration

## Production Deployment

For production deployment:

1. Use `--profile production --profile traefik`
2. Set `DJANGO_DEBUG=0` in `.env`
3. Configure proper `DJANGO_ALLOWED_HOSTS`
4. Use environment-specific `.env` files
5. Set up proper SSL/TLS termination (Traefik handles this)
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
