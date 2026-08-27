# FarmSync Final System Architecture & Engineering Blueprint

**Project**: FarmSync / Intelligent Animal Detection System  
**Document**: Authoritative Architecture Specification  
**Stage**: STEP 18 – Final Architectural Blueprint  
**Status**: APPROVED & ACTIVE  

---

## 1. High-Level Architectural Flow

```
+─────────────────────────────────────────────────────────────────────────+
│                       Presentation Layer (Frontend)                     │
│  - Decoupled Single-Page Application (SPA)                              │
│  - Vanilla HTML5 + CSS3 Glassmorphism System                            │
│  - Centralized ES6 JavaScript ApiClient (api.js + app.js)               │
+────────────────────────────────────┬────────────────────────────────────+
                                     │ HTTP REST (JSON) + JWT Bearer
                                     │ Multipart MJPEG Stream
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
│                    API Gateway & Security Layer                         │
│  - Django REST Framework (DRF) Version 1 Gateway (/api/v1/)             │
│  - SimpleJWT Token Authentication (Access/Refresh/Blacklist)            │
│  - Role-Based Access Control (RBAC: IsAdminOrReadOnly)                  │
│  - Standardized Response Envelope & Exception Interceptor               │
+────────────────────────────────────┬────────────────────────────────────+
                                     │
         ┌───────────────┬───────────┴───┬───────────────┬────────────────┐
         ▼               ▼               ▼               ▼                ▼
   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │ Accounts  │   │  Farmers  │   │Attendance │   │   Tasks   │   │ Dashboard │
   │ App (Auth)│   │ App (CRUD)│   │App (Logs) │   │App (State)│   │ Analytics │
   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │               │               │               │
         └───────────────┴───────────┬───┴───────────────┴───────────────┘
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
│               Computer Vision & Detection Subsystem                     │
│  - Lazy Singleton Cached YOLOv8 Inference Engine                        │
│  - 29 Animal Classes Scored against Threat Hierarchy (High/Med/Low)     │
│  - VideoStreamService (Live MJPEG Stream + OpenCV Frame Acquisition)    │
│  - DetectionService (Snapshot Analysis + Cooldown State Management)     │
+────────────────────────────────────┬────────────────────────────────────+
                                     │
                       ┌─────────────┴─────────────┐
                       ▼                           ▼
               ┌───────────────┐           ┌───────────────┐
               │   AnimalLog   │           │   Immutable   │
               │   Snapshots   │           │ Hazard Alerts │
               └───────┬───────┘           └───────┬───────┘
                       │                           │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
│              Settings & Notification Management Subsystem               │
│  - ProjectSettings Singleton Model (Dynamic Thresholds, Camera Index)   │
│  - EmailSenderConfig (SMTP Dispatcher with Write-Only Password Storage) │
│  - AlertReceiver Management (Active Email Recipients Roster)            │
+────────────────────────────────────┬────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
│                       Data Storage Layer (ORM)                          │
│  - Active Development & Production: backend/db.sqlite3 / PostgreSQL     │
│  - Historical Pre-Migration Archive: legacy/data/data.db (Read-Only)   │
+─────────────────────────────────────────────────────────────────────────+
```

---

## 2. Detailed Component Architecture

### A. Frontend Architecture (Decoupled SPA)
- **Zero Python Template Coupling**: Contains zero server-side Jinja rendering. Can be hosted statically or replaced with React/Vue/Lovable AI without altering backend Python code.
- **Centralized API Client (`frontend/js/api.js`)**: Encapsulates token management (`localStorage`), auto-refresh retry on `401 Unauthorized`, response unwrapping, and standardized error parsing.
- **Brand Glassmorphism System (`frontend/css/style.css`)**: Implements light-green glass panels (`backdrop-filter: blur(16px)`), responsive grids, status badges, and accessible modal forms.

### B. Authentication & RBAC Flow
- **Token Mechanism**: Uses SimpleJWT `HS256` symmetric signing with configurable access token lifetime (default 60 mins) and refresh token lifetime (default 7 days).
- **Token Rotation & Revocation**: Upon refresh, old refresh tokens are rotated and blacklisted, preventing replay attacks.
- **RBAC Policy**:
  - `AllowAny`: Public login and token refresh.
  - `IsAuthenticated`: Read operations on all domain entities for authenticated workers.
  - `IsAdminOrReadOnly`: Restricts POST/PUT/PATCH/DELETE mutations on workforce, tasks, attendance, detection toggle, and settings strictly to staff/admin accounts.

### C. Workforce, Attendance & Task Workflow
- **Farmers CRUD**: Workforce roster stored in `apps.farmers.models.Farmer`.
- **Shift Attendance**: Workers check in with optional device location. Duplicate check-in on the same date is rejected with `400 Bad Request`. Check-out automatically calculates total duration (`total_hours = check_out - check_in`).
- **Tasks Lifecycle**: Tasks transition strictly between `Pending` and `Completed`.
- **Relational Integrity**: Deleting a farmer cascades associated attendance records (`CASCADE`) and safely nullifies task assignments (`SET_NULL`).

### D. YOLO Computer Vision & Hazard Alerting Flow
- **Model Loader (`backend/services/yolo/loader.py`)**: Lazily initializes the YOLOv8 neural network singleton in memory on first inference request, avoiding redundant disk reads per frame.
- **Threat Level Scoring**: Classifies 29 animal species into threat tiers (`high`, `medium`, `low`). Threat levels can be dynamically overridden at runtime via `ProjectSettings`.
- **Alert Dispatch & Cooldown**: High-threat animals trigger `Email + Buzzer` alerts; medium-threat triggers `Email`; low-threat triggers `Log Only`. An in-memory cooldown tracker suppresses repeated alert dispatches within the configured cooldown window (default 60 seconds).
- **Alert Immutability**: Alert records in `apps.alerts.models.Alert` are strictly read-only (`405 Method Not Allowed` on POST/PUT/DELETE) to preserve an untampered historical audit log.

### E. Live Video Streaming & Camera Integration
- **Endpoint**: `GET /api/v1/detection/stream/` returning a Django `StreamingHttpResponse` with `multipart/x-mixed-replace; boundary=frame`.
- **Authentication**: Supports standard `Authorization: Bearer <token>` headers as well as query parameter tokens (`?token=<access_token>`) for standard HTML `<img>` rendering in browsers.
- **Hardware Fallback**: If physical camera hardware is unavailable (e.g. CI/CD or cloud servers), a synthetic placeholder canvas is streamed without throwing unhandled exceptions.

---

## 3. Legacy vs. Django Enhancements Matrix

| Architectural Feature | Classification | Implementation Details |
|---|---|---|
| **API Gateway & Routing** | **DJANGO ENHANCEMENT** | Migrated monolithic Flask routes to versioned DRF router (`/api/v1/`). |
| **JWT Token Security** | **DJANGO ENHANCEMENT** | SimpleJWT with token rotation, blacklist revocation, and RBAC. |
| **YOLO Model Caching** | **DJANGO ENHANCEMENT** | Singleton lazy-loader eliminating redundant model initialization. |
| **Dynamic Settings Singleton** | **DJANGO ENHANCEMENT** | Database-backed runtime settings modifying detection thresholds without restart. |
| **Decoupled SPA Frontend** | **DJANGO ENHANCEMENT** | Replaced server-side Jinja templates with clean, decoupled client application. |
| **29 Animal Classes & Threat Tiers** | **LEGACY-DERIVED** | Faithfully migrated all 29 target animal species from legacy prototype. |
| **Shift Duration Computation** | **LEGACY-DERIVED & ENHANCED** | Preserved check-in/out duration calculation while moving to Django ORM. |
| **Multipart MJPEG Streaming** | **LEGACY-DERIVED & ENHANCED** | Preserved video feed boundary format while adding query-token JWT auth. |
| **Write-Only SMTP Password** | **DJANGO ENHANCEMENT** | Protected sensitive email passwords from exposure in API responses. |
| **Immutable Alert Trail** | **DJANGO ENHANCEMENT** | Enforced read-only security on alert history preventing data tampering. |
