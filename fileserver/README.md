# FileServer

A minimal, secure Django file server that supports browsing, uploads, streaming downloads (with optional compression), share links, CLI tokens, and superadmin user management. The UI follows the Apple-like aesthetic defined in the project specification.

## Requirements

- Python 3.12+
- pip / virtualenv

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install django==5.0.4
   ```

2. Apply migrations:

   ```bash
   python manage.py migrate
   ```

3. Create an initial superuser:

   ```bash
   python manage.py createsuperuser
   ```

4. Create groups and file access rules via the Django admin or the shell. Example:

   ```bash
   python manage.py shell
   >>> from django.contrib.auth.models import Group
   >>> from core.models import FileAccessRule
   >>> devs = Group.objects.create(name="devs")
   >>> FileAccessRule.objects.create(group=devs, path="projects/dev")
   ```

5. Configure the storage root (defaults to `<project>/data/`):

   ```bash
   export FILE_SERVER_ROOT=/absolute/path/to/storage
   ```

6. Run the development server:

   ```bash
   python manage.py runserver
   ```

## Features

- **Authentication** – All routes (except share links) require login. Superadmins see the user management console.
- **File browser** – Browse files/folders under `FILE_SERVER_ROOT`, trigger downloads, archive downloads, uploads, and share links via the inline actions menu.
- **Uploads** – Upload from the browser or via CLI (`curl -F "files=@report.pdf" http://host/upload/projects/dev/`).
- **Streaming downloads** – Files stream directly; folders can be streamed as `.tar.gz` or `.zip` archives.
- **Share links** – Generate expiring public URLs that do not require authentication.
- **CLI tokens** – Temporary tokens for `curl`/`wget` usage (`?token=...`).
- **User management** – Superadmins can create users, reset passwords, toggle activation, assign groups, and delete accounts without using Django admin.

## Testing

Run the automated test suite:

```bash
python manage.py test
```

The tests cover CLI token generation, share link expiry, access control, and download/upload authorization scenarios.

## Configuration

Environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `FILE_SERVER_ROOT` | Base directory for file storage | `<project>/data/` |
| `TOKEN_EXPIRY_HOURS` | Default CLI token lifetime | `1` |
| `SHARE_LINK_EXPIRY_HOURS` | Default share link lifetime | `24` |
| `FILESERVER_DEFAULT_THEME` | Light or dark theme preset | `light` |
| `DJANGO_DEBUG` | Enable Django debug mode (`1` for true) | `0` |

## CLI Examples

```
# Download a file using basic auth
curl -u alice:password http://localhost:8000/download/file/projects/dev/notes.txt

# Download a folder as zip using a token
curl -O "http://localhost:8000/download/folder/projects/dev/?format=zip&token=ABC123"

# Upload via CLI
curl -u alice:password -F "files=@report.pdf" http://localhost:8000/upload/projects/dev/
```

## Light/Dark Mode

Users can toggle light/dark themes from the navbar. The preference is stored in the session.

## Health Check

A simple readiness endpoint is available at `/health/` returning `{"status": "ok"}`.
