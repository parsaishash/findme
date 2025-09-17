

## 1. Overview

_(same as before — skipped here for brevity)_

---

## 2. Frontend Wireframes

### 2.1 Login Page

```
 -------------------------------------------------
 |                     ◯                        |
 |                 [Minimal Logo]                |
 |                                               |
 |               ┌───────────────┐               |
 | Username:     │               │               |
 |               └───────────────┘               |
 |                                               |
 | Password:     │               │               |
 |               └───────────────┘               |
 |                                               |
 |                [  Login Button  ]             |
 |                                               |
 -------------------------------------------------
```

- Centered card with logo above.
    
- Username + password fields stacked.
    
- Minimal button.
    

---

### 2.2 File Explorer (Main Page)

```
[Navbar: ◯  Home / projects / reports                  ☀️  User ▼]

 --------------------------------------------------------------
 | 📁 projects/                     | 2025-09-15    •••       |
 --------------------------------------------------------------
 | 📁 reports/                      | 2025-09-14    •••       |
 --------------------------------------------------------------
 | 📄 readme.txt (1.2 KB)           | 2025-09-12    •••       |
 --------------------------------------------------------------
 | 📄 data.csv (5.8 MB)             | 2025-09-10    •••       |
 --------------------------------------------------------------
 
 [Footer: © 2025 FileServer                       v1.0.0]
```

---

### 2.3 3-Dots Menu (Dropdown)

```
   •••  ▼
   -------------------------
   | Download              |
   | Compress & Download ▶ |
   | Upload (if folder)    |
   | Generate Share Link   |
   | Copy CLI Token URL    |
   -------------------------
```

---

### 2.4 Upload Modal

```
 -----------------------------
 |       Upload File          |
 |-----------------------------|
 |   [ Drag & Drop Here ]     |
 |   or                       |
 |   [ Choose File Button ]   |
 |                             |
 |   Progress: [██████----]    |
 |                             |
 |   [Cancel]     [Upload]     |
 -----------------------------
```

---

### 2.5 Share Link Modal

```
 -----------------------------
 |      Share Link            |
 |-----------------------------|
 | Link:                      |
 | [ http://server/share/abc123 ] [Copy] |
 | Expires: 24h               |
 |                             |
 |   [Close]                   |
 -----------------------------
```

---

### 2.6 Token Modal

```
 -----------------------------
 |   Generate CLI Token       |
 |-----------------------------|
 | Token: x7K9bTq2            |
 | Expires: 1h                |
 |                             |
 | Example:                   |
 | curl -O http://server/files/data.csv?token=x7K9bTq2 |
 |                             |
 |   [Close] [Generate New]    |
 -----------------------------
```

---

### 2.7 Superadmin – User Management Page

```
[Navbar: ◯  Home                                 ☀️  Admin ▼]

 ------------------ User Management ------------------
 
 [ Create New User ]
 -----------------------------------------------------
 | Username   | Group     | Status  | Actions        |
 -----------------------------------------------------
 | alice      | devs      | active  | Reset | Delete |
 | bob        | testers   | active  | Reset | Delete |
 | carol      | managers  | inactive| Activate Delete|
 -----------------------------------------------------

 [Footer: © 2025 FileServer                       v1.0.0]
```

**Create New User Form (Modal or Inline):**

```
 -----------------------------
 |   Create New User          |
 |-----------------------------|
 | Username: [           ]    |
 | Password: [           ]    |
 | Group:    [Dropdown ▼]     |
 | Active:   [x]              |
 |                             |
 |   [Cancel]     [Create]     |
 -----------------------------
```

---

## 3. User Flows (Visualized)

- **Normal user**: Login → File Explorer → 3-dots → Download/Upload/Share → Logout.
    
- **CLI user**: Generate token in modal → Use with curl/wget.
    
- **Superadmin**: Login → File Explorer → “User Management” → Create/manage users.
    

---

✅ Now the spec has **visual wireframes + technical details**.  
This should be a complete blueprint for CodeX to implement both **backend and frontend**.

---

👉 Do you want me to also **design the database models (User, Group, Token, ShareLink, etc.) in this doc** so CodeX has schema guidance too?