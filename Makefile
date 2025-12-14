# Docker Compose commands for FindMe project

.PHONY: help build up down restart logs shell migrate collectstatic test clean

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
build: ## Build Docker images
	docker-compose build

build-prod: ## Build production Docker images
	docker-compose -f docker-compose.yml build

up: ## Start all services in development mode
	docker-compose up -d

up-prod: ## Start all services in production mode
	docker-compose -f docker-compose.yml up -d

up-dev: ## Start services using docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-web: ## Show logs from web service
	docker-compose logs -f web

logs-worker: ## Show logs from celery worker
	docker-compose logs -f celery_worker

shell: ## Open shell in web container
	docker-compose exec web bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec db psql -U findme -d findme

# Django management commands
migrate: ## Run Django migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create Django migrations
	docker-compose exec web python manage.py makemigrations

collectstatic: ## Collect Django static files
	docker-compose exec web python manage.py collectstatic --noinput

createsuperuser: ## Create Django superuser
	docker-compose exec web python manage.py createsuperuser

test: ## Run Django tests
	docker-compose exec web python manage.py test

# Development tools
install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	pre-commit autoupdate

format: ## Format code with black and isort
	black findme/
	isort findme/

lint: ## Run linting checks
	flake8 findme/
	mypy findme/

safety: ## Check for security vulnerabilities in dependencies
	safety check

# Cleanup commands
clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

clean-volumes: ## Remove all volumes
	docker-compose down -v

# Production deployment helpers
prod-deploy: ## Deploy to production (build and start)
	docker-compose -f docker-compose.yml up -d --build

prod-logs: ## Show production logs
	docker-compose -f docker-compose.yml logs -f

# Database operations
db-backup: ## Backup PostgreSQL database
	docker-compose exec db pg_dump -U findme findme > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore PostgreSQL database (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T db psql -U findme -d findme < $(FILE)
