FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install Python dependencies with uv
COPY requirements.txt /app/
RUN uv pip install --system -r requirements.txt

# Copy project files
COPY . /app/

# Create dedicated user and data directory
RUN addgroup --system findme && adduser --system --ingroup findme --home /app findme \
    && mkdir -p /data \
    && chown -R findme:findme /data /app

USER findme

ENV FILE_SERVER_ROOT=/data \
    DJANGO_SETTINGS_MODULE=findme.settings

EXPOSE 8000

CMD ["gunicorn", "findme.wsgi:application", "--bind", "0.0.0.0:8000"]
