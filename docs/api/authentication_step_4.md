# FarmSync Authentication & Authorization Specification (Step 4)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 4 – Authentication & Authorization Layer  
**Date**: August 2026  
**Status**: ACTIVE / VERIFIED  

---

## 1. Authentication Architecture & Overview

The FarmSync backend utilizes **JSON Web Tokens (JWT)** via `djangorestframework-simplejwt` backed by Django's native authentication subsystem (`django.contrib.auth.models.User`).

### Core Architecture Principles
1. **Stateless & Decoupled**: The backend does not maintain server-side session cookies for API consumers. Any decoupled frontend (React, Vite, Vue, mobile apps, or Lovable AI clients) authenticates purely via HTTP `Authorization: Bearer <access_token>` headers.
2. **Standard User Model**: Utilizes Django's standard `User` model, avoiding unnecessary custom model complexities while providing complete support for passwords, email, staff flags, and group permissions.
3. **Dual Token Lifetime**:
   - **Access Token**: Short-lived (60 minutes default), used for authorizing API requests.
   - **Refresh Token**: Long-lived (7 days default), used to obtain a new access token without re-entering credentials.
4. **Token Blacklisting**: Revoked refresh tokens are stored in the database (`token_blacklist`), preventing subsequent token rotations after logout.

---

## 2. Dependencies

| Package | Version Installed | Purpose & Rationale |
| :--- | :--- | :--- |
| `djangorestframework-simplejwt` | `5.5.1` | Industry-standard JWT authentication for Django REST Framework with built-in token rotation and blacklisting support. |
| `PyJWT` | `2.13.0` | Cryptographic signing and token serialization backend for RFC 7519 JSON Web Tokens. |

---

## 3. Authentication Endpoints

### 3.1 Login Endpoint
- **URL**: `POST /api/v1/auth/login/`
- **Permissions**: `AllowAny`
- **Request Body**:
  ```json
  {
    "username": "farmmanager",
    "password": "SecurePassword123!"
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user": {
        "id": 1,
        "username": "farmmanager",
        "email": "manager@farmsync.local",
        "first_name": "Farm",
        "last_name": "Manager",
        "is_staff": true,
        "is_superuser": true,
        "date_joined": "2026-08-24T12:00:00Z",
        "last_login": "2026-08-24T12:30:00Z"
      }
    }
  }
  ```
- **Error Response (`400 Bad Request`)**:
  ```json
  {
    "success": false,
    "message": "Invalid username or password.",
    "errors": {
      "non_field_errors": ["Invalid username or password."]
    }
  }
  ```

---

### 3.2 Token Refresh Endpoint
- **URL**: `POST /api/v1/auth/refresh/`
- **Permissions**: `AllowAny`
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Token refreshed successfully",
    "data": {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```
- **Error Response (`401 Unauthorized`)**:
  ```json
  {
    "success": false,
    "message": "Token is blacklisted",
    "errors": {
      "token": ["Token is blacklisted"]
    }
  }
  ```

---

### 3.3 Current Authenticated User (`/me`)
- **URL**: `GET /api/v1/auth/me/`
- **Permissions**: `IsAuthenticated`
- **Headers Required**: `Authorization: Bearer <access_token>`
- **Success Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Current user profile retrieved successfully",
    "data": {
      "id": 1,
      "username": "farmmanager",
      "email": "manager@farmsync.local",
      "first_name": "Farm",
      "last_name": "Manager",
      "is_staff": true,
      "is_superuser": true,
      "date_joined": "2026-08-24T12:00:00Z",
      "last_login": "2026-08-24T12:30:00Z"
    }
  }
  ```
- **Unauthenticated Response (`401 Unauthorized`)**:
  ```json
  {
    "success": false,
    "message": "Authentication credentials were not provided.",
    "errors": {}
  }
  ```

---

### 3.4 Logout & Token Blacklist Endpoint
- **URL**: `POST /api/v1/auth/logout/`
- **Permissions**: `IsAuthenticated`
- **Headers Required**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Logout successful. Refresh token has been revoked.",
    "data": {}
  }
  ```

---

## 4. Frontend Integration Flow

```text
[Frontend Client / SPA / Lovable AI]
       │
       │  1. POST /api/v1/auth/login/ { username, password }
       ▼
[Django Backend SimpleJWT]
       │
       │  2. Return { access, refresh, user }
       ▼
[Frontend Client]
       │  Store access token in memory / secure storage
       │
       │  3. GET /api/v1/farmers/ (Header: 'Authorization: Bearer <access>')
       ▼
[Protected REST API View]
       │
       │  4. Valid Token -> Process & Return JSON data
       ▼
[Frontend Client]
       │
       │  5. Access token expires -> POST /api/v1/auth/refresh/ { refresh }
       ▼
[Django Backend SimpleJWT]
       │
       │  6. Return new { access, refresh }
       ▼
[Frontend Client]
```

---

## 5. Global Permission Policy

- **Default Permission**: `rest_framework.permissions.IsAuthenticated` is configured globally across the entire Django REST Framework settings.
- **Explicit Public Exemptions**: Only explicitly whitelisted views declare `permission_classes = [AllowAny]`:
  - `GET /api/v1/health/` (Health check)
  - `GET /api/v1/` (API Root discovery)
  - `POST /api/v1/auth/login/` (User login)
  - `POST /api/v1/auth/refresh/` (Token refresh)
- **All future domain APIs** (Farmers, Attendance, Tasks, Settings, Detection, Alerts) will automatically require valid JWT authentication by default.

---

## 6. Development User Creation

To initialize administrative or development users:
```bash
cd backend
python manage.py createsuperuser
```
Prompts will request username, email, and password. Test users within unit tests are created ephemerally in the isolated test database and cleaned up automatically.

---

## 7. Token Security & Privacy Guarantees

1. **Zero Secret Leakage**: Password hashes (`pbkdf2_sha256`), signing keys, and server environment variables are never returned in serialization payloads.
2. **CORS Origin Protection**: Only explicit frontend origins specified in `CORS_ALLOWED_ORIGINS` are accepted.
3. **Blacklist Invalidation**: Revoked refresh tokens cannot be used to forge new sessions.
