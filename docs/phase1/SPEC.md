

## 1. Overview

This project is a **minimal, secure file server** built with Django.  
It allows authenticated users to **browse, download, upload, and share files** from a designated server directory.  
The design philosophy is **minimal and modern (Apple-like)** with **light/dark mode** support.

Key features:

- User authentication & group-based access control.
    
- File browser with Bootstrap UI.
    
- File & folder download (with on-the-fly compression).
    
- Upload support (browser + CLI).
    
- Shareable links with expiry.
    
- Temporary CLI tokens for curl/wget usage.
    
- Superadmin in-app user management.
    

---

## 2. Features

### 2.1 Authentication

- Django auth system for login/logout.
    
- All pages (except share links) require login.
    
- **Superadmin** users have elevated permissions.
    

### 2.2 User Management (Superadmin Only)

- When logged in, superadmin sees an additional **“User Management”** option in the navbar.
    
- Page includes:
    
    - **Create new user** form: username, password, group, active flag.
        
    - List of existing users with options:
        
        - Reset password
            
        - Activate/deactivate
            
        - Assign to group
            
        - Delete
            

_(This avoids visiting Django Admin for daily user operations.)_

### 2.3 Access Control

- Each group has access to certain subfolders.
    
- Users can only browse/upload/download inside their allowed folders.
    
- Superadmin has access to everything.
    

### 2.4 File Browsing

- Tree-like directory listing starting at configured `FILE_SERVER_ROOT`.
    
- UI shows:
    
    - 📁 folders
        
    - 📄 files
        
- Each entry has a **3-dots menu** with actions.
    

### 2.5 Download & Compression

- Direct file download.
    
- Folder downloads:
    
    - Dynamically compressed into `.tar.gz` or `.zip`.
        
    - Streamed (no temp file saved).
        
- CLI support:
    
    ```bash
    wget --user=john --password=secret http://server/download/file/data.csv
    curl -u john:secret -O http://server/download/folder/project/?format=tar.gz
    ```
    

### 2.6 Uploads

- Browser upload via modal (drag & drop or file input).
    
- CLI upload:
    
    ```bash
    curl -u john:secret -F "file=@report.pdf" http://server/upload/projects/reports/
    ```
    

### 2.7 Share Links

- Users can generate a **temporary public link** for a file/folder.
    
- Properties:
    
    - Random unique token.
        
    - Expiry time (default 24h).
        
    - Works without login.
        
- Example:
    
    ```
    http://server/share/abc123/
    ```
    

### 2.8 CLI Short Tokens

- Users can generate a **temporary authentication token** instead of using username/password.
    
- Properties:
    
    - Short random string (e.g., `x7K9bTq2`).
        
    - Expiry time (configurable, default 1h).
        
    - User-specific and scoped to permissions.
        
- Example usage:
    
    ```bash
    wget http://server/download/file/data.csv?token=x7K9bTq2
    curl -O http://server/download/folder/project?token=x7K9bTq2
    ```
    

---

## 3. Technical Design

### 3.1 Tech Stack

- Backend: Django (latest LTS).
    
- Frontend: Bootstrap 5.
    
- Auth: Django built-in.
    
- Compression: Python `tarfile` / `zipfile`.
    
- Deployment: Gunicorn + Nginx.
    

### 3.2 Configuration

- `FILE_SERVER_ROOT`: path on server for file storage.
    
- `TOKEN_EXPIRY_HOURS`: default lifetime for CLI tokens.
    
- `SHARE_LINK_EXPIRY_HOURS`: default lifetime for share links.
    

### 3.3 URL Structure

- `/login/` → Login page.
    
- `/logout/` → Logout.
    
- `/files/` → Root directory browser.
    
- `/files/<path>/` → Subdirectory.
    
- `/download/file/<path>/` → File download.
    
- `/download/folder/<path>?format=tar.gz` → Folder download.
    
- `/upload/<path>/` → File upload.
    
- `/share/<token>/` → Share link.
    
- `/token/new/` → Generate CLI token.
    
- `/admin/users/` → Superadmin user management.
    

### 3.4 Security

- CSRF protection for uploads.
    
- Directory traversal prevention (`../`).
    
- Expired tokens/links return 404.
    
- Group-based folder access.
    

---

## 4. Frontend Design (Minimal Apple-Like)

### 4.1 Global Layout

- **Top Navbar (fixed)**
    
    - Left: minimal logo (monochrome).
        
    - Center: breadcrumb path (`Home / projects / reports`).
        
    - Right:
        
        - Light/Dark mode toggle (☀️ / 🌙).
            
        - User menu (dropdown: Profile, Generate Token, Logout).
            
        - **Superadmin only:** “User Management”.
            
- **Main Content**
    
    - Centered file explorer table.
        
    - Max width: 1200px.
        
    - Rounded corners, subtle dividers.
        
- **Footer**
    
    - Left: `© <year> FileServer`
        
    - Right: version info.
        

---

### 4.2 File Explorer

Clean table (no visible borders):

```
----------------------------------------------------------
| 📁 projects/                 | 2025-09-15   •••         |
----------------------------------------------------------
| 📁 reports/                  | 2025-09-14   •••         |
----------------------------------------------------------
| 📄 readme.txt (1.2 KB)       | 2025-09-12   •••         |
----------------------------------------------------------
| 📄 data.csv (5.8 MB)         | 2025-09-10   •••         |
----------------------------------------------------------
```

- Left: icon + name.
    
- Right: date modified + 3-dots menu.
    

---

### 4.3 3-Dots Menu

- Download
    
- Compress & Download (tar.gz / zip)
    
- Upload (if folder)
    
- Generate Share Link
    
- Copy CLI Token URL
    

---

### 4.4 Modals

- **Upload Modal**: drag & drop or file picker, progress bar.
    
- **Share Link Modal**: shows generated link + expiry.
    
- **Token Modal**: generate token, show example wget/curl command.
    
- **Superadmin User Modal**: create new user, assign group, set password.
    

---

### 4.5 Light & Dark Mode

- Light: white background, dark text, black icons.
    
- Dark: dark background (`#111`), light text, white icons.
    
- Toggle available in navbar.
    

---

### 4.6 Typography & Spacing

- Font: system default (`-apple-system, Roboto, Segoe UI`).
    
- Font sizes:
    
    - Navbar: 16px
        
    - Explorer: 14px
        
- Generous padding (20px in containers).
    
- Subtle shadows for depth.
    

---

## 5. User Flow

### 5.1 Normal User

1. Login → redirected to `/files/`.
    
2. Browse directories.
    
3. Use 3-dots menu to download/upload/share.
    
4. Generate CLI token from user menu if needed.
    

### 5.2 Superadmin

1. Login → redirected to `/files/`.
    
2. Extra “User Management” menu in navbar.
    
3. Manage users (create, reset password, deactivate, delete).
    

### 5.3 CLI

- Auth with username/password:
    
    ```bash
    wget --user=alice --password=1234 http://server/download/file/data.csv
    ```
    
- Auth with token:
    
    ```bash
    wget http://server/download/file/data.csv?token=abc123
    ```
    

---

## 6. Future Enhancements (Phase 2)

- API endpoints for automation.
    
- Inline file previews (PDF, images, text).
    
- Search and filter in file explorer.
    
- Expiring **share links with password protection**.
    
- Drag-and-drop uploads into explorer view.
    
- File versioning/history.
    
