
# Project Structure & Best Practices

## 1. Overall Layout

```
fileserver/
├── manage.py
├── fileserver/                # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                      # Core app: auth, tokens, share links, admin UI
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/core/...
│   └── static/core/...
├── browser/                   # File browser app
│   ├── __init__.py
│   ├── models.py (optional: logs, etc.)
│   ├── views.py
│   ├── urls.py
│   ├── forms.py (upload form)
│   ├── templates/browser/...
│   └── static/browser/...
├── users/                     # Custom user management (superadmin tools)
│   ├── __init__.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/users/...
│   └── static/users/...
└── docs/phase1/               # Documentation (SPEC.md, WIREFRAME.md, etc.)
```

---

## 2. Best Practices

### 2.1 Views

- Use **class-based views** (CBVs) with Django’s **generic views**:
    
    - `TemplateView` for static pages (login, dashboard).
        
    - `ListView` / custom for file listings.
        
    - `FormView` for uploads.
        
    - `DetailView` for share link/token details.
        
- Extend with mixins for auth (`LoginRequiredMixin`, `UserPassesTestMixin`).
    

Example:

```python
from django.views.generic import TemplateView, ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

class FileBrowserView(LoginRequiredMixin, TemplateView):
    template_name = "browser/file_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files"] = get_directory_listing(self.kwargs.get("path", ""))
        return context
```

---

### 2.2 Templates

- Use **base.html** with Bootstrap and light/dark mode toggle.
    
- Extend base for all pages (`{% extends "base.html" %}`).
    
- Separate templates per app (`templates/browser/`, `templates/core/`, `templates/users/`).
    

---

### 2.3 Static & Media

- Place CSS/JS in `static/`.
    
- Use Bootstrap 5 via CDN.
    
- Keep custom CSS minimal (for Apple-like design + dark mode).
    

---

### 2.4 URLs

- `fileserver/urls.py` → include app urls.
    
- Apps define their own urls in `urls.py`.
    

Example:

```python
urlpatterns = [
    path("files/", include("browser.urls")),
    path("users/", include("users.urls")),
    path("", include("core.urls")),
]
```

---

### 2.5 Models

- Keep **token & share link models** in `core/models.py`.
    
- File logs (upload/download) can live in `browser/models.py`.
    
- User extension handled with Django groups (no custom user model unless needed).
    

---

### 2.6 Security

- Use `LoginRequiredMixin` for all protected views.
    
- Validate file paths against `FILE_SERVER_ROOT`.
    
- Use `StreamingHttpResponse` for large downloads.
    
- Enforce expiry checks on tokens & share links.
    

---

### 2.7 Forms

- Define Django forms for:
    
    - File upload (`forms.FileField`).
        
    - Create/edit user (superadmin).
        
    - Generate tokens/share links.
        
- Forms should use Bootstrap form classes (`form-control`, `btn btn-primary`).
    

---

### 2.8 Testing

- Unit tests for:
    
    - Token validation.
        
    - Share link expiry.
        
    - Group-based access.
        
    - Uploads/downloads.
        
- Use Django’s `TestCase` + temporary directories.
    

---

## 3. Suggested Apps & Responsibilities

- **core** → login/logout, CLI tokens, share links, base templates.
    
- **browser** → file explorer, downloads, uploads, logs.
    
- **users** → superadmin-only user management (create/edit/delete users).
    

---

## 4. Deployment Notes

- Use Gunicorn or uWSGI behind Nginx.
    
- Configure `FILE_SERVER_ROOT` in `settings.py`.
    
- Collect static files with `python manage.py collectstatic`.
    
- Environment variables for secrets & paths.
    
