# FarmSync – Intelligent Farm Monitoring & Smart Agricultural Management System

**Project**: FarmSync / Intelligent Animal Intrusion Detection & Agricultural Workforce Management System  
**Architecture**: Decoupled API-First Django REST Framework Backend + Modern React 19 / Vite SPA Frontend + YOLOv8 Neural Vision Engine  
**Status**: **PRODUCTION-READY & FULLY VERIFIED (159 / 159 Backend Tests Passing & Production Frontend Built)**  
**License**: MIT  

---

## 1. Executive Summary & Problem Solved

Traditional agricultural monitoring systems suffer from two major operational bottlenecks:
1. **Crop & Livestock Vulnerability**: Wild animal intrusions (e.g., elephants, wolves, bears, lions, wild boars) cause severe crop destruction, livestock predation, equipment damage, and human-wildlife conflict.
2. **Fragmented Workforce Management**: Manual attendance, unverified field assignments, and unstructured paper task tracking lead to operational inefficiencies and payroll discrepancies.

**FarmSync** solves these challenges through a unified, decoupled, enterprise-grade architecture that integrates real-time **Computer Vision (YOLOv8 + OpenCV)** hazard detection with smart **Agricultural Workforce Management (Farmers Roster, Geolocation Attendance, and Task Lifecycle Tracking)**.

---

## 2. System Architecture & Communication Flow

FarmSync uses a modern decoupled architecture where the user interface operates independently from the backend API gateway:

```
                     +-------------------------------------------------------+
                     |             Web Browser Client (SPA)                  |
                     |  Modern React 19 + TypeScript + Vite 8 + Tailwind v4  |
                     |  TanStack Router + TanStack Query v5 + Radix UI       |
                     |  Running on: http://localhost:8080 (or :5173)         |
                     +-------------------------------------------------------+
                                        │                           │
                   REST API (JSON)      │                           │ Multipart MJPEG
                   + JWT Bearer Tokens  │                           │ Video Stream
                                        ▼                           ▼
                     +-------------------------------------------------------+
                     |           Django REST Framework Gateway               |
                     |           Base URL: /api/v1/ | Port: 8000             |
                     |           SimpleJWT Auth (Rotation + Blacklist)       |
                     |           Role-Based Access Control (RBAC)            |
                     +-------------------------------------------------------+
                                        │
        ┌──────────────┬────────────────┼──────────────┬────────────────┐
        ▼              ▼                ▼              ▼                ▼
  ┌───────────┐  ┌───────────┐    ┌───────────┐  ┌───────────┐    ┌───────────┐
  │ Accounts  │  │  Farmers  │    │Attendance │  │   Tasks   │    │ Dashboard │
  │   & RBAC  │  │   CRUD    │    │  Logging  │  │ Management│    │ Analytics │
  └─────┬─────┘  └─────┬─────┘    └─────┬─────┘  └─────┬─────┘    └─────┬─────┘
        │              │                │              │                │
        └──────────────┴────────────────┼──────────────┴────────────────┘
                                        ▼
                     +-------------------------------------------------------+
                     |            Detection & Vision Subsystem               |
                     |   Lazy-Loaded Cached YOLOv8 Singleton Engine          |
                     |   29 Target Animal Species Scored (3 Threat Tiers)    |
                     |   Real-Time MJPEG Streamer + Snapshot Persistence     |
                     +──────────────────┬────────────────────────────────────+
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                 ┌──────────────┐              ┌──────────────┐
                 │  AnimalLog   │              │ Immutable    │
                 │  Snapshots   │              │ Hazard Alerts│
                 └──────┬───────┘              └──────┬───────┘
                        │                             │
                        └──────────────┬──────────────┘
                                       ▼
                     +-------------------------------------------------------+
                     |            ProjectSettings Singleton                  |
                     |   Dynamic Thresholds, Camera Device Index             |
                     |   SMTP Email Dispatcher & Hardware Buzzer Trigger     |
                     |   Customizable Threat Notification Email Templates   |
                     +──────────────────┬────────────────────────────────────+
                                        │
                                        ▼
                     +-------------------------------------------------------+
                     |             Database Storage (ORM)                    |
                     |   Active: backend/db.sqlite3 (PostgreSQL Ready)       |
                     |   Archived: legacy/data/data.db (Frozen Evidence)     |
                     +-------------------------------------------------------+
```

---

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend SPA** | React 19, TypeScript, Vite 8, TanStack Router, TanStack Query v5, Tailwind CSS v4, Radix UI primitives, Lucide React icons, Sonner toast notifications |
| **Backend REST API** | Python 3.11+, Django 5.0+, Django REST Framework 3.14+, SimpleJWT (Token Rotation & Blacklisting), Django-CORS-Headers |
| **Computer Vision** | Ultralytics YOLOv8 Nano (`yolov8n.pt`), OpenCV, Pillow, NumPy |
| **Real-Time Streaming** | Low-latency multipart MJPEG streaming (`multipart/x-mixed-replace`) with token-based query authentication |
| **Hardware & Alerts** | Hardware audio siren buzzer (`warning_sound.mp3`), Automated SMTP Email dispatch with write-only credentials |
| **Database & Storage** | Django ORM with SQLite (`backend/db.sqlite3`), PostgreSQL-ready connection pooling |

---

## 4. Key Functional Modules

| Module | REST Endpoint Base | Key Capabilities | Access Level |
|---|---|---|---|
| **Authentication** | `/api/v1/auth/` | JWT login, profile retrieval (`/me/`), token refresh with rotation, and blacklist logout. | Public Login / Authenticated Profile |
| **Dashboard** | `/api/v1/dashboard/` | Real-time aggregate KPIs (total workers, present today, pending tasks, hazard alerts) & consolidated activity feed. | Authenticated |
| **Farmers** | `/api/v1/farmers/` | Registered farm workforce roster, assigned sectors, contact details. Full CRUD support. | Authenticated (Read) / Staff (Write) |
| **Attendance** | `/api/v1/attendance/` | Shift check-in with GPS location, duplicate check-in blocking, shift check-out, duration computation, and multi-day reports. | Authenticated (Read) / Staff (Write) |
| **Tasks** | `/api/v1/tasks/` | Agricultural task assignments linked to farmers. Strict status transitions (`Pending` ↔ `Completed`). | Authenticated (Read) / Staff (Write) |
| **Live Camera** | `/api/v1/detection/stream/` | Low-latency multipart MJPEG live video feed supporting Bearer headers and query token for browser streaming. | Authenticated |
| **AI Detection** | `/api/v1/detection/` | Manual snapshot image analysis with YOLOv8, real-time threat level scoring (`HIGH`, `MEDIUM`, `LOW`), engine status, and master toggle. | Authenticated / Staff (Toggle) |
| **Detection Logs**| `/api/v1/detection/logs/` | Historical animal intrusion events, species, confidence scores, field locations, timestamps, and snapshot images. | Authenticated |
| **Hazard Alerts** | `/api/v1/alerts/` | Immutable historical audit trail of automated notification dispatches (`Email + Buzzer`, `Email`, `Log Only`). Read-only. | Authenticated (Read-Only) |
| **Settings** | `/api/v1/settings/` | Global runtime singleton for confidence threshold, alert cooldown, camera device index, hourly wage, write-only SMTP password, and alert recipients. | Authenticated (Read) / Staff (Write) |
| **Email Templates** | `/api/v1/settings/email-templates/` | Dynamic HTML/text email templates for High/Medium/Low alerts with syntax validation, live preview, and default reset. | Authenticated (Read) / Staff (Write) |

---

## 5. How to Run This Project (Step-by-Step Guide)

### 1. Prerequisites
Ensure the following tools are installed on your machine:
- **Python**: Python 3.11.x or 3.12.x ([Download Python](https://www.python.org/downloads/))
- **Node.js**: Node.js 18.x or 20.x with `npm` ([Download Node.js](https://nodejs.org/))
- **Git**: For version control
- **Webcam (Optional)**: Built-in or USB camera (Index 0). *The system automatically uses a simulated stream fallback if no physical camera is connected.*

---

### 2. Quick Start: Running the Full Decoupled Stack

To run both the **Django REST Backend** and the **React 19 Frontend**, open **two separate terminal windows**.

#### Terminal 1: Start the Django Backend

From the project root (`AnimalDetection-main`):

```bash
# 1. Activate the Python virtual environment
# Windows (PowerShell):
.\env\Scripts\Activate.ps1
# Windows (CMD):
.\env\Scripts\activate.bat
# macOS / Linux:
source env/bin/activate

# 2. Navigate to the backend directory
cd backend

# 3. Install backend dependencies (if not installed)
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Start the Django backend development server
python manage.py runserver 0.0.0.0:8000
```
> *(Note: If you are already inside the `backend` directory, activate with `..\env\Scripts\Activate.ps1` or `source ../env/bin/activate`)*  
> The Django backend is now active at **`http://localhost:8000`** with the REST API at **`http://localhost:8000/api/v1/`**.

---

#### Terminal 2: Start the React Frontend

From the project root (`AnimalDetection-main`):

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install frontend dependencies (if not installed)
npm install

# 3. Start the Vite development server
npm run dev
```
> The React frontend is now live at **`http://localhost:8080`** (or **`http://localhost:5173`**).

---

### 3. Accessing the Running Applications & Default Logins

| Interface | URL | Default Credentials |
|---|---|---|
| 🌿 **FarmSync Modern Web App** | [http://localhost:8080](http://localhost:8080) | `admin` / `admin123` *(Administrator)*<br>`farm_manager` / `manager123` *(Staff)*<br>`farmer_john` / `worker123` *(Worker)* |
| 🔌 **Django REST API Gateway** | [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/) | Interactive browsable DRF API documentation. |
| 🛠️ **Django Admin Portal** | [http://localhost:8000/admin/](http://localhost:8000/admin/) | `admin` / `admin123` *(Direct database admin access)* |
| 🚀 **Integrated Launchpad Bridge** | [http://localhost:8000/](http://localhost:8000/) | Root server landing page linking to web app & API. |

> [!TIP]
> **Pre-configured Login Details**: A full list of default accounts, roles, and permissions is also documented in [docs/setup/APPLICATION_ACCESS_AND_CREDENTIALS.md](file:///c:/Users/yuvas/Desktop/AnimalDetection-main/docs/setup/APPLICATION_ACCESS_AND_CREDENTIALS.md).

---

### 4. Running in Production / Single-Server Mode

To build the optimized static production bundle for the frontend:
```bash
# From the frontend/ directory:
npm run build

# Preview the production build locally:
npm run preview
```

---

### 5. Running Automated Tests

#### Backend Automated Test Suite (159 Tests)
From the `backend/` directory:
```bash
python manage.py test
```
*Expected Output:* `Ran 159 tests in ~96s - OK` (100% passing).

To run module-specific targeted test suites:
```bash
python manage.py test apps.accounts     # Auth & JWT lifecycles
python manage.py test apps.farmers      # Workforce roster CRUD
python manage.py test apps.attendance   # Check-in/out & reporting
python manage.py test apps.tasks        # Task lifecycle
python manage.py test apps.detection    # YOLO inference & streaming
python manage.py test apps.alerts       # Immutable hazard alerts
python manage.py test apps.settings_app # Runtime project settings & email templates
python manage.py test apps.dashboard    # Analytics & summary KPIs
```

#### Frontend Code Quality & Build Checks
From the `frontend/` directory:
```bash
npm run lint          # Run ESLint validation (0 errors)
npm run format        # Run Prettier code formatting
npm run build         # Verify TypeScript & Vite production build
```

---

## 6. AI Detection & Threat Classification Matrix

FarmSync's lazy-loaded YOLOv8 singleton analyzes incoming camera frames and manual image uploads against 29 animal classes, categorizing each into automated threat tiers:

| Threat Level | Target Species | Automated Dispatch Channels |
|---|---|---|
| 🚨 **HIGH THREAT** | Elephant, Bear, Wolf, Lion, Leopard, Crocodile, Tiger, Wild Dog, Boar | **Audio Buzzer Siren (`warning_sound.mp3`) + Priority SMTP Email Alert with Evidence Snapshot** |
| ⚠️ **MEDIUM THREAT** | Wild Boar, Monkey, Fox, Snake, Coyote, Porcupine | **Automated SMTP Email Alert with Evidence Snapshot** |
| ℹ️ **LOW / BENIGN** | Cow, Sheep, Horse, Bird, Dog, Cat, Zebra, Giraffe | **Logged to Historical Database (`AnimalLog`)** with evidence snapshot |

- **Live Stream Endpoint**: `GET /api/v1/detection/stream/?token=<jwt_access_token>`
- **Manual Image Analysis**: `POST /api/v1/detection/analyze/` (`multipart/form-data`)
- **Evidence Snapshot Download**: `GET /api/v1/alerts/<id>/evidence/download/`

---

## 7. Environment Variables Configuration

A global template is provided in [.env.example](file:///c:/Users/yuvas/Desktop/AnimalDetection-main/.env.example).

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Secret cryptographic key for Django session and token signing | `django-insecure-dev-key` |
| `DJANGO_DEBUG` | Enable/disable debug mode (`True` for local development) | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed host header domains | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins for the React SPA | `http://localhost:8080,http://localhost:5173` |
| `JWT_ACCESS_EXPIRATION_MINUTES` | Access token lifespan in minutes | `60` |
| `JWT_REFRESH_EXPIRATION_DAYS` | Refresh token lifespan in days | `7` |
| `CAMERA_DEVICE_INDEX` | Hardware camera device index (0 for default webcam, 1/2 for external USB) | `0` |
| `ENABLE_LOCAL_AUDIO_BUZZER` | Enable audio playback on high threat intrusions | `True` |
| `SMTP_SERVER` | Outgoing SMTP mail server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_SENDER_EMAIL` | Sender email address for automated alert notifications | `alerts@farmsync.local` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base origin of the Django REST backend (without `/api/v1`) | `http://localhost:8000` |

---

## 8. Complete Project Documentation Index

For complete architectural blueprints, database schemas, and examiner verification materials, consult the structured `docs/` directory:

### Setup & Credentials
- [Developer Setup & Running Guide](docs/setup/PROJECT_SETUP_AND_RUN_GUIDE.md) – Step-by-step developer installation and local execution guide.
- [Application Access & Credentials Guide](docs/setup/APPLICATION_ACCESS_AND_CREDENTIALS.md) – Pre-configured user accounts, roles, and CLI superuser creation.

### Architecture & System Blueprints
- [System Architecture Blueprint](docs/architecture/FINAL_SYSTEM_ARCHITECTURE.md) – End-to-end system architecture, singleton engines, and data flow.
- [Frontend Architecture Specification](docs/architecture/FRONTEND_ARCHITECTURE.md) – React 19, TanStack Router/Query, and state design.
- [Threat Notification Architecture](docs/architecture/THREAT_NOTIFICATION_ARCHITECTURE.md) – 3-tier threat pipeline, hardware buzzer, and SMTP dispatcher.
- [Database Schema & ER Blueprint](docs/architecture/DATABASE_SCHEMA.md) – Full PostgreSQL/SQLite relational schema and table definitions.
- [Legacy Architecture Assessment](docs/architecture/ARCHITECTURE_ASSESSMENT.md) – Architectural comparison of legacy Flask vs Django REST.

### REST API Specifications
- [REST API Endpoint Index](docs/api/API_INDEX.md) – Complete index of all active REST API endpoints.
- [Consolidated API Contract](docs/api/API_CONTRACT.md) – Exhaustive request/response JSON schemas for all modules.
- Per-Module Detailed Specifications: `docs/api/endpoints/` (Alerts, Attendance, Auth, Camera, Dashboard, Detection, Farmers, Settings, Tasks).

### Features & Security
- [Threat Classification & Alerts System](docs/features/THREAT_CLASSIFICATION_AND_ALERTS.md) – Animal threat rules, hardware buzzer siren, evidence snapshots, and dynamic email template system.

### Quality Assurance & Verification
- [Deployment Readiness & Security Specification](docs/qa/DEPLOYMENT_READINESS.md) – Production hardening, environment isolation, and secret management.
- [Frontend Integration Testing Report](docs/qa/FRONTEND_INTEGRATION_TESTING.md) – Full test results for React frontend integration.
- [End-to-End QA Validation](docs/qa/END_TO_END_QA.md) – Cross-module test audit and workflow verification.
- [Feature Parity Verification](docs/qa/FEATURE_PARITY_VERIFICATION.md) – Comprehensive feature parity matrix across all user views.
- [Final Repository Cleanup Report](docs/qa/FINAL_REPOSITORY_CLEANUP_REPORT.md) – Final repository audit, package removals, and status matrix.

### Submission & Archive
- [Final Submission Checklist](docs/submission/FINAL_SUBMISSION_CHECKLIST.md) – Project deliverables & defense readiness.
- [Milestone Reports Archive](docs/archive/milestone_reports/) – Preserved Step 1–21 historical milestone reports for Viva evidence.
- [Legacy Application Archive Documentation](legacy/README.md) – Architectural mapping and provenance for the archived Flask prototype.

---

## 9. Troubleshooting & FAQ

| Issue | Cause | Solution |
|---|---|---|
| **CORS Error in Browser Console** | Backend does not allow the frontend origin. | Ensure `CORS_ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:8080` (or `http://localhost:5173`). |
| **HTTP 401 Unauthorized** | Missing or expired JWT token. | Log in via the web interface or call `/api/v1/auth/login/` to receive a fresh token. |
| **HTTP 403 Forbidden on Write Operations** | Non-staff user attempting mutation. | Sign in with a staff/superuser account to create or edit records. |
| **Webcam Stream Shows Fallback Frame** | No physical camera connected or index mismatch. | The system gracefully falls back to a simulated stream. To switch devices, navigate to **Settings** and update `Camera Hardware Index` to `1` or `2`. |
| **Port 8000 or 8080 Already in Use** | Another service is using the port. | Backend: `python manage.py runserver 8001`. Frontend: Vite will automatically select the next available port. |

---

## 10. Repository Structure

```
AnimalDetection-main/
├── backend/                  # Django REST API Backend Root
│   ├── apps/                 # 9 Modular Django Domain Apps
│   │   ├── core/             # Health checks, response envelopes, RBAC
│   │   ├── accounts/         # User auth, JWT token views, profiles
│   │   ├── farmers/          # Workforce roster models, serializers, views
│   │   ├── attendance/       # Worker attendance logging, check-in/out
│   │   ├── tasks/            # Agricultural task assignment & lifecycle
│   │   ├── detection/        # VideoStreamService, DetectionService, AnimalLog
│   │   ├── alerts/           # Immutable hazard alert history & evidence snapshots
│   │   ├── settings_app/     # ProjectSettings singleton & EmailTemplates
│   │   └── dashboard/        # Aggregate analytics and activity feeds
│   ├── config/               # Settings, WSGI, ASGI, and Root URL Gateway
│   ├── media/                # Detection snapshot storage (media/detections/)
│   ├── services/             # Specialized Python Engines (YOLO loader & Threat classification)
│   ├── manage.py             # Django CLI entrypoint
│   └── requirements.txt      # Backend Python dependencies
├── frontend/                 # Decoupled React 19 SPA (Vite + TypeScript)
│   ├── src/                  # Components, routes, hooks, lib, types
│   │   ├── components/       # Radix UI, layout, KPI cards, tables
│   │   ├── hooks/            # TanStack Query domain hooks (use-api.ts)
│   │   ├── lib/              # Centralized API client (api.ts), auth context
│   │   ├── routes/           # TanStack file-based routes (8 active views)
│   │   └── types/            # DRF TypeScript contracts
│   ├── index.html            # SPA HTML entrypoint
│   ├── package.json          # Frontend dependencies and scripts
│   ├── vite.config.ts        # Vite 8 build pipeline
│   └── README.md             # Frontend technical specification
├── docs/                     # Canonical System Documentation
│   ├── setup/                # Setup & credential access guides
│   ├── architecture/         # System blueprints & schema documentation
│   ├── api/                  # API index, contract, and endpoint specifications
│   ├── features/             # Threat classification, alerts & email templates
│   ├── qa/                   # Deployment readiness, QA audits & cleanup report
│   ├── submission/           # Final submission & Viva checklist
│   └── archive/              # Preserved milestone reports & migration audits
├── static/                   # Brand logos and assets
├── legacy/                   # Archived Legacy Flask Application (Viva Evidence)
├── yolov8n.pt                # YOLOv8 Nano neural network weights file
├── warning_sound.mp3         # Hardware audio buzzer alert sound
├── .env.example              # Global environment configuration template
├── README.md                 # Master project documentation
└── LICENSE                   # MIT License
```
