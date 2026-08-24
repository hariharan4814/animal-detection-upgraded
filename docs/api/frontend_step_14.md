# FarmSync Frontend Integration & API UI Specification (Step 14)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 14 – Frontend Integration & Django API UI Migration  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Architectural Summary & Scope

The **Frontend Presentation Layer** (`frontend/`) provides a fully decoupled Single-Page Application (SPA) that communicates with the Django backend strictly through version 1 REST APIs (`/api/v1/`).

### Key Architectural Decisions:
1. **Decoupled Architecture with Zero Backend Duplication**: Contains zero business calculations in JavaScript. All data, metrics, permissions, and YOLO computer vision inferences originate from the Django backend.
2. **Centralized REST API Client (`frontend/js/api.js`)**: Encapsulates JWT authentication, local token storage, automatic Bearer header attachment, automatic token refresh retries on `401 Unauthorized`, response unwrapping, and standardized error parsing.
3. **Green Glassmorphism Design System (`frontend/css/style.css`)**: Reuses and elevates the brand identity (`--primary: #10b981;`, blurred glass panels, responsive grids, status badges, and accessible modal forms).
4. **Role-Based UX Controls**: Safely hides or disables privileged administrative controls (e.g. settings PATCH, farmer delete, detection toggle) for regular workers, while the Django backend remains the definitive security authority.
5. **Universal Deployment Readiness**: Can be served directly via Django at `http://localhost:8000/` (via `TemplateView`) or hosted independently (Static hosting / Lovable AI ready).

---

## 2. API Endpoints Integration Matrix

| UI Module / View | REST API Endpoints | HTTP Methods | Permissions | Frontend Integration Status |
|---|---|---|---|---|
| **Authentication** | `/api/v1/auth/login/`<br>`/api/v1/auth/refresh/`<br>`/api/v1/auth/me/`<br>`/api/v1/auth/logout/` | POST<br>POST<br>GET<br>POST | AllowAny<br>AllowAny<br>Authenticated<br>Authenticated | **INTEGRATED & VERIFIED** |
| **Dashboard** | `/api/v1/dashboard/summary/`<br>`/api/v1/dashboard/recent-activity/` | GET<br>GET | Authenticated | **INTEGRATED & VERIFIED** |
| **Farmers** | `/api/v1/farmers/`<br>`/api/v1/farmers/{id}/` | GET, POST<br>GET, PUT, PATCH, DELETE | Authenticated (Read)<br>Staff/Admin (Write) | **INTEGRATED & VERIFIED** |
| **Attendance** | `/api/v1/attendance/`<br>`/api/v1/attendance/check-in/`<br>`/api/v1/attendance/check-out/`<br>`/api/v1/attendance/report/` | GET<br>POST<br>POST<br>GET | Authenticated (Read)<br>Staff/Admin (Check-in/out) | **INTEGRATED & VERIFIED** |
| **Tasks** | `/api/v1/tasks/`<br>`/api/v1/tasks/{id}/` | GET, POST<br>GET, PUT, PATCH, DELETE | Authenticated (Read)<br>Staff/Admin (Write) | **INTEGRATED & VERIFIED** |
| **Live Monitoring** | `/api/v1/detection/stream/`<br>`/api/v1/detection/status/`<br>`/api/v1/detection/analyze/` | GET (MJPEG)<br>GET, PATCH<br>POST | Authenticated (Stream, Status, Analyze)<br>Staff/Admin (Toggle) | **INTEGRATED & VERIFIED** |
| **Detection Logs** | `/api/v1/detection/logs/`<br>`/api/v1/detection/logs/{id}/` | GET<br>GET | Authenticated | **INTEGRATED & VERIFIED** |
| **Hazard Alerts** | `/api/v1/alerts/`<br>`/api/v1/alerts/{id}/` | GET<br>GET | Authenticated (Immutable Read-Only) | **INTEGRATED & VERIFIED** |
| **Settings** | `/api/v1/settings/`<br>`/api/v1/settings/email-sender/`<br>`/api/v1/settings/receivers/`<br>`/api/v1/settings/receivers/{id}/` | GET, PATCH<br>GET, PUT<br>GET, POST<br>GET, PUT, DELETE | Authenticated (Read)<br>Staff/Admin (Write) | **INTEGRATED & VERIFIED** |

---

## 3. Frontend Component Structure

```
frontend/
├── index.html       # Single Page Application HTML shell with 8 view sections & modals
├── css/
│   └── style.css    # Green glassmorphism tokens, responsive layout, cards, badges
└── js/
    ├── api.js       # Centralized REST API client with JWT refresh & error handling
    └── app.js       # Application controller, view switching, form handlers, modals
```

---

## 4. Security & Secret Protection

- **No Passwords or Secrets in Frontend**: Zero secrets (such as `SECRET_KEY`, JWT keys, database credentials, or SMTP app passwords) are stored or visible in frontend code.
- **Write-Only SMTP Password**: When updating email configuration, the password field is submitted as write-only and is never displayed back to the client.
- **Strict Read-Only Alerts**: The Alerts view intentionally omits mutation controls (no delete, acknowledge, or dismiss buttons), enforcing the verified immutable audit trail.
