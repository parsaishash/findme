
## 1. Overview

_(same as before — minimal Apple-like file server with auth, downloads, uploads, tokens, share links, superadmin user management)_

---

## 2. Core Models

### 2.1 User (Django Built-in)

- We use Django’s `User` model (or a custom extension via `AbstractUser`).
    
- Fields (default):
    
    - `username` (str, unique)
        
    - `password` (hashed)
        
    - `email` (optional)
        
    - `is_active` (bool)
        
    - `is_superuser` (bool)
        
    - `groups` (many-to-many with Group)
        

### 2.2 Group (Django Built-in)

- Used for folder-level access control.
    
- Fields:
    
    - `name` (str, unique)
        
    - `permissions` (default Django)
        

### 2.3 FileAccessRule (Custom)

- Maps **groups → directories**.
    
- Example: group `devs` can access `/projects/dev`.
    

```python
class FileAccessRule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    path = models.CharField(max_length=512)  # relative to FILE_SERVER_ROOT
```

---

## 3. Token & Share Models

### 3.1 CLIToken

- Temporary token for CLI (`curl`, `wget`).
    
- One-to-many relationship with user.
    

```python
class CLIToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cli_tokens")
    token = models.CharField(max_length=32, unique=True)  # short random string
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
```

- **Validation**:
    
    - Token valid if `now < expires_at` and `is_active=True`.
        
    - Token inherits user’s group permissions.
        

---

### 3.2 ShareLink

- Temporary public download link (no login required).
    

```python
class ShareLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="share_links")
    token = models.CharField(max_length=64, unique=True)  # UUID or short hash
    path = models.CharField(max_length=512)  # file/folder path relative to FILE_SERVER_ROOT
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
```

- **Validation**:
    
    - Link valid if `now < expires_at` and `is_active=True`.
        
    - Expired links return 404.
        

---

## 4. Optional Models (Phase 2 Enhancements)

### 4.1 UploadLog

- Tracks uploads for auditing.
    

```python
class UploadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    path = models.CharField(max_length=512)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField()
```

### 4.2 DownloadLog

- Tracks downloads for auditing.
    

```python
class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=512)
    is_share_link = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField()
```

---

## 5. Relationships

- **User ↔ Group** → default Django M2M.
    
- **Group ↔ FileAccessRule** → One group can have many folder rules.
    
- **User ↔ CLIToken** → One user can generate many tokens.
    
- **User ↔ ShareLink** → One user can generate many share links.
    

---

## 6. Example Data

### Groups & Access

- Group: `devs` → `/projects/dev`
    
- Group: `testers` → `/projects/test`
    
- Group: `managers` → `/reports`
    

### Tokens

- User `alice` → token `x7K9bTq2` → expires 1h.
    

### Share Links

- User `bob` → `/reports/summary.pdf` → link `/share/abc123` → expires 24h.
    

---

## 7. User Flows with Models

### 7.1 CLI Token

1. User generates token → record in `CLIToken`.
    
2. Request arrives with `?token=...`.
    
3. Backend checks `CLIToken` validity → fetch user → check `FileAccessRule`.
    

### 7.2 Share Link

1. User generates share link → record in `ShareLink`.
    
2. Public request arrives at `/share/<token>`.
    
3. Backend checks validity → serve file/folder (no login required).
    

### 7.3 Superadmin User Creation

1. Superadmin uses frontend form → backend calls `User.objects.create_user()`.
    
2. Assign to group via `user.groups.add()`.
    
3. User now inherits group folder access.
    

---

## 8. Wireframes (from earlier)

_(Login, File Explorer, 3-dots menu, Upload Modal, Share Modal, Token Modal, Superadmin User Management)_

---

✅ With this addition, CodeX now has:

- Backend logic.
    
- Database schema.
    
- Frontend layout.
    
- User flows.
    
- Wireframes.
    

---

👉 Do you also want me to include **REST-like pseudo endpoints** (views + expected request/response for each URL) in the docs, or do we stop at models + wireframes?