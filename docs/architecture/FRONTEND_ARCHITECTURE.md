# FarmSync Architecture: Step 19 Frontend Replacement & Backend Integration

## 1. Executive Summary

In Step 19, the legacy vanilla JavaScript frontend was replaced with a modern, production-grade **Lovable AI** user interface. The new frontend is built with **React 19**, **TypeScript**, **Vite 8**, **TanStack Router / Start**, **TanStack Query v5**, **Tailwind CSS v4**, **Radix UI**, and **Lucide React**.

The frontend communicates with the active **Django REST Framework (DRF)** backend via JWT-authenticated REST APIs and an authenticated MJPEG video stream with zero feature loss and full schema alignment.

---

## 2. Decoupled Architecture & Communication Model

```
+-----------------------------------------------------------------------+
|                         FARMSYNC FRONTEND (Vite / React 19)          |
|                                                                       |
|  [ Routes / Pages ]                                                   |
|    * Login & Session Guard                                            |
|    * Dashboard (KPIs, Live Status, Activity Feed)                     |
|    * Farmers Directory (CRUD, Card Grid, Dialogs)                     |
|    * Attendance (Check-in/Out Console, Shifts, Date Filter Reports)   |
|    * Task Management (CRUD, Status Toggle, Farmer Assignment)         |
|    * AI Monitoring (MJPEG Stream Player, YOLO Manual Upload Inference)|
|    * Detection Logs (Historical Feed, Snapshot Sheet Drawer)          |
|    * Hazard Alerts (Immutable Audit Feed, Threat Badges)              |
|    * Settings (Project Settings, SMTP Sender, Alert Receivers)        |
|                                                                       |
|  [ TanStack Query Layer & API Client (src/lib/api.ts) ]               |
|    * Bearer Token Injection & Storage (localStorage)                  |
|    * Automatic Silent Token Refresh on 401 (/api/v1/auth/refresh/)    |
|    * Response Envelope Unpacking ({ success, message, data })         |
|    * Standardized Field Error Parser                                  |
+-----------------------------------+-----------------------------------+
                                    |
            REST API (JSON)         |   MJPEG Video Stream (?token=...)
        (http://localhost:8000/api/v1/)  (http://localhost:8000/api/v1/detection/stream/)
                                    v
+-----------------------------------------------------------------------+
|                         FARMSYNC BACKEND (Django 5.0 + DRF)           |
|                                                                       |
|  * JWT Auth Gateway (/api/v1/auth/)                                   |
|  * Workforce Engine (/api/v1/farmers/, /api/v1/attendance/)           |
|  * Task Scheduler (/api/v1/tasks/)                                    |
|  * YOLOv8 Vision Engine & MJPEG Streamer (/api/v1/detection/)         |
|  * Automated Alert Dispatcher (/api/v1/alerts/)                       |
|  * System Configuration & SMTP Service (/api/v1/settings/)            |
|  * Root Gateway & Static Bridge (/)                                   |
+-----------------------------------------------------------------------+
```

---

## 3. Directory Structure

```
AnimalDetection-main/
├── backend/                  # Django REST Framework Backend
│   ├── apps/
│   │   ├── accounts/         # SimpleJWT Auth & User Profiles
│   │   ├── alerts/           # Immutable Hazard Alerts Engine
│   │   ├── attendance/       # Check-in, Check-out, Report Aggregation
│   │   ├── core/             # Health, Root Gateway, Custom Exception Handler
│   │   ├── dashboard/        # Summary KPI & Recent Activity Feeds
│   │   ├── detection/        # YOLOv8 Vision Pipeline & MJPEG Stream
│   │   ├── farmers/          # Workforce Directory CRUD
│   │   ├── settings_app/     # Runtime Settings, SMTP Sender, Alert Receivers
│   │   └── tasks/            # Agricultural Task Planning & Tracking
│   └── config/               # Settings, URLs, ASGI, WSGI
├── frontend/                 # Lovable AI React 19 Frontend
│   ├── public/               # Favicon, robots.txt
│   ├── src/
│   │   ├── components/       # Radix UI primitives, Layout, KpiCards, States
│   │   ├── hooks/            # TanStack Query domain hooks (use-api.ts)
│   │   ├── lib/              # api.ts, auth.tsx, format.ts, utils.ts
│   │   ├── routes/           # TanStack file-based routes
│   │   │   ├── __root.tsx    # Root shell, Providers, Sonner Toaster
│   │   │   ├── login.tsx     # JWT Login Screen
│   │   │   ├── app.tsx       # Authenticated layout with collapsible sidebar
│   │   │   ├── app.index.tsx # Dashboard command center
│   │   │   ├── app.farmers.tsx
│   │   │   ├── app.attendance.tsx
│   │   │   ├── app.tasks.tsx
│   │   │   ├── app.monitoring.tsx
│   │   │   ├── app.detection-logs.tsx
│   │   │   ├── app.alerts.tsx
│   │   │   └── app.settings.tsx
│   │   └── types/            # api.ts (DRF TypeScript contracts)
│   ├── index.html            # Django template & SPA entry bridge
│   ├── package.json          # Vite & dependencies
│   ├── tsconfig.json         # TypeScript strict configuration
│   └── vite.config.ts        # Vite 8 build pipeline
```

---

## 4. Key Data Contracts & Schema Alignments

| Domain | DRF Backend Contract | Frontend Implementation |
|---|---|---|
| **Response Envelope** | `{ success: bool, message: str, data: T }` | `apiRequest<T>` unwraps `data` property automatically |
| **Error Format** | `{ success: false, errors: { field: [msg] } }` | `humanizeError` and `ApiError.fieldErrors` mapping |
| **Farmer** | `{ id, name, phone, field, email, is_active }` | Form validates `name`, `phone`, `field`, optional `email` |
| **Attendance Check-In** | POST `/api/v1/attendance/check-in/` `{ farmer_id, device_location }` | `useAttendanceActions.checkIn` sends `{ farmer_id, device_location }` |
| **Attendance Report** | GET `/api/v1/attendance/report/?start_date=&end_date=&farmer_id=` | Date range filter controls + KPI hours summary |
| **Tasks** | `{ id, task_name, status: "Pending"\|"Completed", assigned_to, date }` | Status toggle, worker assignment Select, date picker |
| **Detection Status** | GET/PATCH `/api/v1/detection/status/` `{ detection_enabled: bool }` | Master Switch with live camera stream player |
| **Image Analysis** | POST `/api/v1/detection/analyze/` (multipart `image`, `field`) | Drag & drop file upload with progress bar & threat level |
| **Email Sender** | PUT `/api/v1/settings/email-sender/` (`smtp_host`, `smtp_port`, `smtp_password` [write-only]) | Write-only password input with `smtp_password_configured` status badge |
| **Receivers** | `{ id, name, email, is_active, receive_animal_alerts, receive_attendance_reports }` | Modal CRUD with toggle checkboxes |
| **Alerts** | GET `/api/v1/alerts/` (Read-only) | Immutable event audit feed with snapshot Sheet drawer |

---

## 5. Security & Session Management

1. **JWT Rotation**: `SimpleJWT` issues 60-minute access tokens and 7-day refresh tokens.
2. **Automatic Silent Refresh**: On any `401 Unauthorized` response, `apiRequest` invokes `/api/v1/auth/refresh/` transparently before retrying the queued request.
3. **Session Expiry Hook**: If refresh fails or tokens are invalidated, the local session is cleared and the user is redirected to `/login`.
4. **Stream Token Authentication**: The MJPEG camera stream uses `?token=<access_token>` in image source attributes because browser `<img>` elements cannot supply `Authorization: Bearer` headers.
5. **Write-Only Passwords**: `smtp_password` is write-only on the backend and never exposed in API responses.
