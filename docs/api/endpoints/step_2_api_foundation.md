# FarmSync REST API Foundation Specification (Step 2)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 2 – Core API Foundation  
**Version**: 1.0 (API Namespace: `/api/v1/`)  
**Date**: August 2026  
**Status**: ACTIVE / FOUNDATION VERIFIED  

---

## 1. API Base Path & Global Routing

All REST API resources in the FarmSync backend are namespaced under a global versioned path:

```text
Base URL: /api/v1/
```

### URL Routing Hierarchy
- Root URLconf (`backend/config/urls.py`): Maps `/api/v1/` to the modular application routers.
- Core URLconf (`backend/apps/core/urls.py`): Exposes API entry points, discovery metadata, and health monitoring endpoints.

---

## 2. API Versioning Strategy

- **Strategy**: URL Path Versioning (`/api/v1/`).
- **Rationale**: 
  - URL path versioning provides unambiguous, explicit endpoint targeting for independent frontend SPAs, mobile applications, and third-party integrations (e.g. Lovable AI clients).
  - Breaking schema changes in future iterations will be introduced under `/api/v2/` without disrupting legacy client connections.

---

## 3. Core Endpoints

### 3.1 Health Check Endpoint
- **Route**: `GET /api/v1/health/`
- **Authentication**: None (`AllowAny`)
- **Purpose**: Real-time operational uptime and readiness check for frontend clients, reverse proxies (Nginx), and container orchestrators.
- **Security Guarantee**: Zero environment variables, database strings, SMTP credentials, or server file paths are exposed.

#### Response (`200 OK`)
```json
{
  "success": true,
  "message": "FarmSync backend API is operational",
  "data": {
    "status": "healthy",
    "service": "FarmSync REST API",
    "version": "v1"
  }
}
```

---

### 3.2 API Root Discovery Endpoint
- **Route**: `GET /api/v1/`
- **Authentication**: None (`AllowAny`)
- **Purpose**: Returns metadata regarding active API version, documentation locations, and core discovery links.

#### Response (`200 OK`)
```json
{
  "success": true,
  "message": "Welcome to FarmSync REST API v1",
  "data": {
    "name": "FarmSync API",
    "version": "v1",
    "status": "operational",
    "documentation": "/docs/api/step_2_api_foundation.md",
    "endpoints": {
      "health": "/api/v1/health/"
    }
  }
}
```

---

## 4. Standard Response & Error Conventions

All API responses follow a strict, deterministic JSON envelope contract.

### 4.1 Success Response Envelope
```json
{
  "success": true,
  "message": "Human-readable summary of the operation result.",
  "data": {
    "key": "value"
  }
}
```

### 4.2 Error Response Envelope
```json
{
  "success": false,
  "message": "Detailed error summary or validation alert.",
  "errors": {
    "field_name": [
      "Validation error description for this field."
    ]
  }
}
```

---

## 5. HTTP Status Code Principles

The backend utilizes strict RESTful HTTP status code semantics:

| HTTP Status | Semantic Meaning | Usage in FarmSync API |
| :--- | :--- | :--- |
| `200 OK` | Request Succeeded | Successful data retrieval (`GET`), update (`PUT`/`PATCH`), or operational health check. |
| `201 Created` | Resource Created | Successful creation of a farmer, task, or setting entity (`POST`). |
| `204 No Content` | Action Completed Without Body | Successful deletion of a resource (`DELETE`). |
| `400 Bad Request` | Request / Validation Error | Malformed request body, invalid field format, or constraint failure. |
| `401 Unauthorized` | Authentication Required | Missing, invalid, or expired JWT bearer token (Future Step 4). |
| `403 Forbidden` | Permission Denied | Authenticated user lacks RBAC privileges for the requested resource. |
| `404 Not Found` | Resource Not Found | Target endpoint or database record does not exist. |
| `500 Internal Server Error` | Unexpected Server Error | Unhandled backend exception; returns sanitized message without leaking traces. |

---

## 6. Global Exception Handling Strategy

The core API registers a global exception handler (`apps.core.exceptions.custom_exception_handler`) in Django REST Framework.

### Key Capabilities:
1. **DRF Validation Formatting**: Converts Django and DRF field-level errors into the standard `errors` dictionary.
2. **HTTP 404 Interception**: Intercepts `Http404` and `NotFound` exceptions to return standard JSON rather than default HTML error pages.
3. **HTTP 500 Sanitization**: Catches unhandled exceptions, logs full stack traces internally to server logs via Python's `logging` module, and returns a safe, sanitized generic error message to the client.

---

## 7. Cross-Origin Resource Sharing (CORS) Strategy

To enable independent frontend development (e.g. Vite dev servers, Next.js, or Lovable AI prototypes):
- **Middleware**: `corsheaders.middleware.CorsMiddleware` placed at the top of the Django middleware pipeline.
- **Configurability**: Configured dynamically via the `CORS_ALLOWED_ORIGINS` environment variable.
- **Security Policy**: Wildcard origins (`CORS_ALLOW_ALL_ORIGINS = True`) are **disabled**. Only explicit origins defined in `.env` are permitted.
- **Credentials Support**: `CORS_ALLOW_CREDENTIALS = True` enabled for secure authorization headers.

### Configuring Frontend Origins
In `backend/.env`:
```bash
# Comma-separated list of allowed frontend origins
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,https://my-lovable-app.lovable.app
```

---

## 8. Environment Configuration Reference

| Environment Variable | Description | Default / Development Value |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | Cryptographic secret for signing sessions and tokens | Insecure dev fallback (Must change in production) |
| `DJANGO_DEBUG` | Controls debug trace output and static media routing | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed host header domains | `localhost,127.0.0.1` |
| `DJANGO_TIME_ZONE` | Server timezone identifier | `UTC` (or `Asia/Kolkata`) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of permitted frontend client URLs | `http://localhost:3000,http://localhost:5173,...` |
| `DATABASE_URL` | Database connection URI | `sqlite:///db.sqlite3` |

---

## 9. Current Authentication Status

> ⚠️ **IMPORTANT NOTE**: Authentication and user authorization have **NOT YET BEEN MIGRATED**.
> Currently, core foundation endpoints (`/api/v1/health/`, `/api/v1/`) are configured with `AllowAny` for infrastructure verification. Full JSON Web Token (JWT) authentication and Role-Based Access Control (RBAC) will be implemented systematically during **STEP 4**.

---

## 10. Rules for Future Frontend Integration

Any future frontend application (including Lovable AI-generated interfaces) must adhere to these rules:
1. **Target Versioned API**: Make all requests to `/api/v1/...`.
2. **Handle Standard Envelopes**: Expect responses with `success`, `message`, and either `data` or `errors`.
3. **No Direct Database Queries**: All data manipulation must occur via documented REST endpoints.
4. **CORS Origin Registration**: Ensure the frontend host domain is added to `CORS_ALLOWED_ORIGINS` in the backend environment.
