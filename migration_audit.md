# STEP 0: Migration Audit & Comprehensive System Inventory

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 0 – Audit & Architecture Assessment (Analysis Only)  
**Date**: August 2026  
**Auditor**: Antigravity AI – Advanced Agentic Coding Assistant  
**Status**: COMPLETED (Analysis Only – No source files modified, no folders created)

---

## 1. Executive Summary

This document presents the complete architectural, functional, security, and dependency audit for the **FarmSync / Intelligent Animal Detection** project. The project currently operates as a prototype-level, monolithic Flask application combining Computer Vision (YOLOv8 + OpenCV), hardware camera capture, automated notification dispatch (SMTP email and local audio buzzer), farm workforce management (farmer registration, geolocation-tagged attendance logging), and task delegation into a single runtime.

The target architecture is a **fully decoupled, API-First backend and frontend system**. The future backend will be powered by **Django and Django REST Framework (DRF)**, structured into modular domain applications (`accounts`, `core`, `settings_app`, `dashboard`, `farmers`, `attendance`, `tasks`, `detection`, `alerts`) supported by isolated backend service engines (`services/yolo`, `services/camera`, `services/notifications`). The frontend will be completely decoupled into a standalone client application capable of being replaced by modern Single-Page Applications (SPAs), including Lovable AI-generated interfaces, without modifying backend business logic.

### Key Audit Findings
1. **Coupling Status**: **HIGHLY COUPLED**. Flask routes directly render Jinja2 HTML templates, embed raw SQLite queries, trigger blocking background processes (SMTP email and audio playback) inside the video streaming loop, and rely on browser-level form POST redirects.
2. **Authentication & Authorization**: **COMPLETELY ABSENT**. The current application has zero authentication, zero user session management, zero password verification, and no Role-Based Access Control (RBAC). All routes and operations are publicly accessible.
3. **Security Vulnerabilities**:
   - Hard-coded SMTP credentials present in source code (`app.py`).
   - Direct raw SQL queries throughout route controllers without ORM schema enforcement or query validation.
   - Synchronous network calls in the video frame loop leading to denial-of-service/frame freezing when alerts trigger.
4. **AI & Vision Pipeline**: YOLOv8 Nano (`yolov8n.pt`) operates over OpenCV `VideoCapture(0)`. While functional, the camera capture and model loading are bound to a global instance at module import time, preventing multi-worker WSGI/ASGI deployment.
5. **Frontend Replacement Readiness**: **NOT READY (in current state)**. The frontend cannot currently be replaced because no RESTful API layer exists. Completing Steps 1 through 14 of the migration roadmap will achieve 100% decoupling readiness.

---

## 2. Current Project Architecture

### 2.1 Monolithic Flask Structure
The existing repository follows a classic monolithic Flask architecture:
- **Application Controller (`app.py`)**: Acts as a central orchestrator. It imports configuration, initializes the global `VideoStreaming` object, configures routes, runs raw SQL queries, and renders Jinja2 HTML templates.
- **Database Access (`database/db.py`)**: Uses direct `sqlite3` driver connections, manual row-factory settings, and raw SQL queries (`execute_query`, `execute_update`) against `data.db`.
- **Domain Modules (`modules/`)**:
  - `animal_detection.py`: Contains `AnimalDetectionSystem` (YOLO inference, bounding boxes, snapshot generation) and `VideoStreaming` (OpenCV camera capture generator).
  - `alerts.py`: Handles alert record logging, MIME email generation with attachments via `smtplib`, and local sound playback via `pygame.mixer`.
  - `attendance.py`: Manages check-in/out logic, duration calculation, and attendance confirmation emails.
  - `tasks.py`: Implements task creation and status updates.
- **Presentation Layer (`templates/` and `static/`)**: 7 Jinja2 HTML templates styled with a custom 341-line Vanilla CSS green glassmorphism design system (`static/style.css`).

### 2.2 Architectural Coupling Bottlenecks
```text
┌────────────────────────────────────────────────────────────────────────┐
│                   CURRENT MONOLITHIC ARCHITECTURE                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   Client Browser                                                       │
│         ▲                                                              │
│         │  HTTP GET / POST (Form Submissions & Full Page Reloads)      │
│         ▼                                                              │
│   Flask Controller (app.py)                                            │
│   ├── Direct Route Handlers                                            │
│   ├── Embedded Raw SQL (execute_query)                                 │
│   ├── Jinja2 Template Rendering (render_template)                      │
│   ├── Global VideoStreaming Object (cv2.VideoCapture(0))               │
│   └── Synchronous Alert Dispatch                                       │
│         │                                                              │
│         ├──► SQLite3 (data.db)                                         │
│         ├──► YOLOv8 Model (yolov8n.pt via ultralytics)                 │
│         ├──► Blocking SMTP Email Dispatch (smtplib)                    │
│         ├──► Blocking Local Audio Buzzer (pygame.mixer)                │
│         └──► Local File System Image Dump (static/detected_*.jpg)      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. File and Directory Inventory

| File / Directory | Size / Lines | Purpose | Current Layer | Target Migration Destination | Action Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `app.py` | 172 lines / 6.5 KB | Main Flask router, controllers, global video stream, hardcoded email config | Backend / Mixed | `/backend/apps/` & `/backend/config/` | Refactor into modular Django views, serializers, and URL routers |
| `config.json` | 52 lines / 1.1 KB | Dynamic animal threat level rules (46 animals), work start time, wage rate | Configuration | `/backend/apps/settings_app/` | Migrate to Django database models with seed fixtures |
| `data.db` | 28 KB binary | SQLite database storing farmers, attendance, tasks, animal_logs, alerts | Backend Data | `/backend/data.db` (via Django ORM) | Migrate schema to Django ORM migrations and models |
| `yolov8n.pt` | 6.55 MB binary | YOLOv8 Nano PyTorch model weights | Backend AI Asset | `/backend/services/yolo/weights/` | Relocate to backend YOLO service weights folder |
| `warning_sound.mp3` | 109 KB binary | Alert audio buzzer file for high-threat animal detections | Backend Asset | `/backend/media/audio/` | Relocate to backend media storage for buzzer service |
| `requirements.txt` | 14 lines / 234 B | Python package dependencies list | Configuration | `/backend/requirements.txt` | Update: remove Flask packages; add Django, DRF, CORS, JWT |
| `README.md` | 101 lines / 4.6 KB | Repository documentation & setup guide | Documentation | `/docs/` & Root README | Update for Django backend & decoupled frontend setup |
| `run.txt` | 85 lines / 3.4 KB | Legacy run notes, threat mapping definitions, class arrays | Documentation / Scratch | `/docs/` | Archive in documentation folder |
| `review1.txt` | 0 B | Empty scratch file | Scratch | Delete / Archive | Clean up during file structure setup |
| `.gitignore` | 19 lines / 202 B | Git ignore rules for Python, VSCode, env | Configuration | Root `.gitignore` | Update with Django, media, frontend node_modules ignores |
| `LICENSE` | 21 lines / 1.1 KB | MIT open-source license text | Legal / Docs | Root `LICENSE` | Retain at repository root |
| `database/` | Directory | Database access package | Backend | `/backend/apps/` | Replaced entirely by Django ORM |
| `database/__init__.py` | 0 B | Package marker | Backend | N/A | Superseded by Django app structure |
| `database/db.py` | 104 lines / 2.8 KB | SQLite connection, table DDL creation, execute_query helpers | Backend | `/backend/apps/*/models.py` | Replace with Django ORM models and migrations |
| `modules/` | Directory | Backend domain logic modules | Backend | `/backend/apps/` & `/backend/services/` | Refactor into Django apps and dedicated services |
| `modules/__init__.py` | 0 B | Package marker | Backend | N/A | Superseded by Django packages |
| `modules/alerts.py` | 87 lines / 3.6 KB | Email sending (smtplib), buzzer playback (pygame), alert queries | Backend | `/backend/apps/alerts/` & `/backend/services/notifications/` | Refactor into asynchronous notification service |
| `modules/animal_detection.py` | 130 lines / 5.2 KB | YOLO detection system, frame processing, video streaming generator | Backend | `/backend/apps/detection/` & `/backend/services/yolo/` | Refactor into backend detection service & camera service |
| `modules/attendance.py` | 88 lines / 3.9 KB | Check-in/out logic, hours calculation, email notifications | Backend | `/backend/apps/attendance/` & `/backend/services/notifications/` | Refactor into attendance Django app with DRF serializers |
| `modules/tasks.py` | 18 lines / 695 B | Task creation, status updates, task listing | Backend | `/backend/apps/tasks/` | Refactor into tasks Django app with DRF viewsets |
| `templates/` | Directory | Server-rendered Jinja2 HTML templates | Frontend | `/frontend/` | Redesign into API-consuming decoupled SPA components |
| `templates/dashboard.html` | 56 lines / 2.2 KB | Main dashboard statistics cards | Frontend | `/frontend/src/views/Dashboard` | Replace with frontend SPA component consuming stats API |
| `templates/farmers.html` | 85 lines / 4.0 KB | Farmer workforce list & creation form | Frontend | `/frontend/src/views/Farmers` | Replace with frontend SPA component consuming `/api/farmers/` |
| `templates/attendance.html` | 110 lines / 5.2 KB | Attendance check-in/out actions & today's logs | Frontend | `/frontend/src/views/Attendance` | Replace with frontend SPA component consuming attendance API |
| `templates/attendance_report.html` | 98 lines / 4.9 KB | Date-range filtered attendance reports | Frontend | `/frontend/src/views/Reports` | Replace with frontend SPA component consuming reports API |
| `templates/tasks.html` | 84 lines / 4.1 KB | Task delegation form & task status board | Frontend | `/frontend/src/views/Tasks` | Replace with frontend SPA component consuming tasks API |
| `templates/camera.html` | 80 lines / 3.6 KB | Live camera stream display & detection toggle buttons | Frontend | `/frontend/src/views/Camera` | Replace with frontend SPA component consuming stream & toggle APIs |
| `templates/alerts.html` | 62 lines / 2.7 KB | History table of detected animals & snapshots | Frontend | `/frontend/src/views/Alerts` | Replace with frontend SPA component consuming detection log API |
| `static/` | Directory | Static assets (CSS, JS, images) | Frontend Asset | `/frontend/public/` & `/frontend/src/` | Relocate static assets to decoupled frontend |
| `static/style.css` | 341 lines / 6.0 KB | Custom green glassmorphism CSS design system | Frontend Asset | `/frontend/src/styles/` | Retain as master design system stylesheet for SPA |
| `static/script.js` | 81 lines / 1.6 KB | Orphaned jQuery camera adjustment handlers | Frontend Asset | Deprecate | Replace with modern API client service in frontend |
| `static/green_glass_hero.png` | 49.2 KB binary | Hero background image | Frontend Asset | `/frontend/public/assets/` | Move to frontend public assets |
| `static/green_glass_decorative.png`| 554.7 KB binary | Brand logo / decorative glass graphic | Frontend Asset | `/frontend/public/assets/` | Move to frontend public assets |
| `_source/` | Directory | Legacy design assets | Docs / Asset | `/docs/architecture/assets/` | Relocate to docs architecture assets |
| `_source/layout.jpg` | 63.7 KB binary | UI layout reference diagram | Docs / Asset | `/docs/architecture/assets/` | Relocate to docs architecture assets |

---

## 4. Feature Inventory

| Feature Name | Status in Code | Current Implementation File(s) | Current Layer | Database Usage | External Dependencies | Hardware Dependencies | Frontend Dependency | Migration Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard Overview** | IMPLEMENTED | `app.py`, `dashboard.html` | Shared/Mixed | `farmers`, `attendance`, `alerts`, `tasks` | SQLite3 | None | Jinja2 template (`dashboard.html`) | LOW |
| **User Authentication** | NOT FOUND | None | None | None | None | None | None | MEDIUM (Requires new `accounts` app) |
| **Role-Based Authorization** | NOT FOUND | None | None | None | None | None | None | MEDIUM (Admin vs Worker roles) |
| **User Management** | NOT FOUND | None | None | None | None | None | None | MEDIUM (CRUD for user profiles) |
| **Farmer Management** | IMPLEMENTED | `app.py`, `farmers.html`, `database/db.py` | Shared/Mixed | `farmers` table | SQLite3 | None | Form POST & Jinja2 loop | LOW |
| **Attendance Check-In** | IMPLEMENTED | `app.py`, `modules/attendance.py`, `attendance.html` | Shared/Mixed | `attendance`, `farmers` | `smtplib` | Geolocation API | HTML Form + Geolocation JS | LOW |
| **Attendance Check-Out** | IMPLEMENTED | `app.py`, `modules/attendance.py`, `attendance.html` | Shared/Mixed | `attendance`, `farmers` | `smtplib` | Geolocation API | HTML Form + Geolocation JS | LOW |
| **Working Hours Calculation** | IMPLEMENTED | `modules/attendance.py` | Backend | `attendance` table | None | None | Jinja2 template formatting | LOW |
| **Attendance Date Reporting** | IMPLEMENTED | `app.py`, `attendance_report.html` | Shared/Mixed | `attendance`, `farmers` | SQLite3 | None | HTML Form POST & Jinja2 loop | LOW |
| **Geolocation Logging** | IMPLEMENTED | `attendance.html`, `attendance.py` | Shared/Mixed | `attendance.location` | None | Browser GPS / Geolocation | HTML5 Geolocation JS | LOW |
| **Task Assignment** | IMPLEMENTED | `app.py`, `modules/tasks.py`, `tasks.html` | Shared/Mixed | `tasks`, `farmers` | SQLite3 | None | HTML Form POST & Jinja2 | LOW |
| **Task Status Updating** | IMPLEMENTED | `app.py`, `modules/tasks.py`, `tasks.html` | Shared/Mixed | `tasks` table | SQLite3 | None | HTML Form POST button | LOW |
| **Camera Hardware Capture** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | OpenCV (`cv2`) | USB/Integrated Webcam (Index 0) | `<img src="/video_feed">` | HIGH (Concurrency & isolation) |
| **Live MJPEG Video Stream** | IMPLEMENTED | `app.py`, `modules/animal_detection.py`, `camera.html` | Shared/Mixed | None | OpenCV, Flask Response | Webcam | `<img src="/video_feed">` | MEDIUM |
| **Camera Feed Toggle** | IMPLEMENTED | `app.py`, `modules/animal_detection.py`, `camera.html` | Shared/Mixed | None | None | None | Inline JS Fetch (`/toggle_camera`)| LOW |
| **Detection Feed Toggle** | IMPLEMENTED | `app.py`, `modules/animal_detection.py`, `camera.html` | Shared/Mixed | None | None | None | Inline JS Fetch (`/toggle_detection`)| LOW |
| **YOLO Model Loading** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | `ultralytics`, `torch` | CPU / CUDA GPU | None | MEDIUM (Singleton management) |
| **Animal Detection Inference** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | `ultralytics`, `numpy`, `cv2` | Webcam | Bounding box on stream | MEDIUM |
| **Confidence Thresholding** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | Hardcoded (`conf > 0.5`)| None | None | LOW (Move to dynamic settings) |
| **Threat Classification** | IMPLEMENTED | `modules/animal_detection.py`, `config.json` | Backend | None | `config.json` | None | None | LOW (Move to dynamic DB rules) |
| **Detection Image Snapshot** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | OpenCV (`cv2.imwrite`) | Local Filesystem | Path stored in DB | LOW (Move to Django media) |
| **Detection Event Logging** | IMPLEMENTED | `modules/animal_detection.py` | Backend | `animal_logs` table | SQLite3 | None | Jinja2 loop (`alerts.html`) | LOW |
| **Alert Cooldown Mechanism** | IMPLEMENTED | `modules/animal_detection.py` | Backend | None | Time module (`300s`) | None | None | LOW (Move to dynamic DB setting) |
| **Email Alert Notifications** | IMPLEMENTED | `modules/alerts.py`, `app.py` | Backend | `alerts` table | `smtplib`, MIME | Internet / SMTP server | None | MEDIUM (Make async/non-blocking) |
| **Multiple Email Recipients** | IMPLEMENTED | `modules/alerts.py`, `app.py` | Backend | None | Comma-separated parsing | SMTP server | None | LOW (Move to DB-managed model) |
| **Audio Buzzer Alert** | IMPLEMENTED | `modules/alerts.py` | Backend | `alerts` table | `pygame.mixer` | Host Audio Output/Speakers | None | HIGH (Server headless support) |
| **Dynamic Settings Management**| PARTIAL | `config.json` (Read-only at startup) | Backend | None | JSON file | None | None | MEDIUM (Requires full CRUD API) |

---

## 5. Complete Flask Route Inventory

| Current Flask Route | HTTP Method(s) | Flask Function | Purpose | Request Input | Response Type | Template Used | Database Interaction | Auth Protection | Recommended API Migration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | `dashboard()` | Render dashboard overview with aggregate statistics | None | HTML (Jinja2) | `dashboard.html` | SELECT COUNT on `farmers`, `attendance`, `alerts`, `tasks` | None | `GET /api/dashboard/stats/` (Pure API) |
| `/camera` | `GET` | `camera_page()` | Render camera viewing and control interface | None | HTML (Jinja2) | `camera.html` | None | None | Frontend SPA Route `/camera` |
| `/attendance` | `GET` | `attendance_page()` | Render attendance management and daily logs | None | HTML (Jinja2) | `attendance.html` | SELECT on `attendance`, `farmers` | None | `GET /api/attendance/logs/` (Pure API) |
| `/tasks` | `GET` | `tasks_page()` | Render task management board and farmer assignment | None | HTML (Jinja2) | `tasks.html` | SELECT on `tasks`, `farmers` | None | `GET /api/tasks/` (Pure API) |
| `/alerts` | `GET` | `alerts_page()` | Render animal detection history and snapshots | None | HTML (Jinja2) | `alerts.html` | SELECT on `animal_logs` | None | `GET /api/detection/logs/` (Pure API) |
| `/video_feed` | `GET` | `video_feed()` | Stream live camera frames with bounding boxes | None | Multipart MJPEG Stream | None | None (Triggered by detection engine) | None | `GET /api/detection/camera/stream/` (Streaming API) |
| `/toggle_detection` | `GET` | `toggle_detection()` | Toggle YOLO inference on/off in video stream | None | JSON | None | None | None | `POST /api/detection/camera/detection/toggle/` |
| `/toggle_camera` | `GET` | `toggle_camera()` | Toggle camera hardware feed active/blank | None | JSON | None | None | None | `POST /api/detection/camera/toggle/` |
| `/check_in` | `POST` | `check_in()` | Record farmer check-in timestamp and GPS coordinates | Form: `farmer_id`, `device_location` | 302 Redirect to `/attendance` | None | INSERT into `attendance`, SELECT `farmers` | None | `POST /api/attendance/check-in/` (Pure API) |
| `/check_out` | `POST` | `check_out()` | Record farmer check-out and compute total hours | Form: `farmer_id`, `device_location` | 302 Redirect to `/attendance` | None | UPDATE `attendance`, SELECT `farmers` | None | `POST /api/attendance/check-out/` (Pure API) |
| `/add_task` | `POST` | `add_new_task()` | Assign a new work task to a farmer | Form: `task_name`, `assigned_to` | 302 Redirect to `/tasks` | None | INSERT into `tasks` | None | `POST /api/tasks/` (Pure API) |
| `/update_task` | `POST` | `update_task()` | Update status of a task to 'Completed' | Form: `task_id`, `status` | 302 Redirect to `/tasks` | None | UPDATE `tasks` | None | `PATCH /api/tasks/{id}/status/` (Pure API) |
| `/attendance_report` | `GET`, `POST` | `attendance_report()` | Filter attendance records by start and end dates | Form (POST): `start_date`, `end_date` | HTML (Jinja2) | `attendance_report.html` | SELECT on `attendance` JOIN `farmers` with date WHERE | None | `GET /api/attendance/reports/?start_date=...&end_date=...` |
| `/farmers` | `GET` | `manage_farmers()` | List all registered farm workers | None | HTML (Jinja2) | `farmers.html` | SELECT on `farmers` | None | `GET /api/farmers/` (Pure API) |
| `/add_farmer` | `POST` | `add_farmer()` | Register a new farmer in the workforce | Form: `name`, `phone`, `field`, `email` | 302 Redirect to `/farmers` | None | INSERT into `farmers` | None | `POST /api/farmers/` (Pure API) |
| `/delete_farmer/<int:farmer_id>` | `POST` | `delete_farmer(farmer_id)` | Remove a farmer from the system | URL Param: `farmer_id` | 302 Redirect to `/farmers` | None | DELETE from `farmers` | None | `DELETE /api/farmers/{id}/` (Pure API) |

---

## 6. Database Audit

### 6.1 Database Engine & Connection Analysis
- **Engine**: SQLite3 (`data.db`).
- **Connection Management**: Direct `sqlite3.connect('data.db', check_same_thread=False)` inside `database/db.py`.
- **Query Architecture**: Raw SQL strings formatted with `?` parameters. No query builder, no validation, and no migration history table.

### 6.2 Existing Entity Audit & Django ORM Mapping

#### Table 1: `farmers`
- **Current Schema**:
  ```sql
  CREATE TABLE farmers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT NOT NULL,
      field TEXT NOT NULL,
      email TEXT
  );
  ```
- **Current Rows**: 1 record.
- **Relationships**: Parent of `attendance.farmer_id` and `tasks.assigned_to`.
- **Recommended Django Model**: `Farmer` in `apps.farmers.models`
  - `id`: `models.BigAutoField(primary_key=True)`
  - `name`: `models.CharField(max_length=150)`
  - `phone`: `models.CharField(max_length=20)`
  - `email`: `models.EmailField(blank=True, null=True)`
  - `field_location`: `models.CharField(max_length=150)`
  - `created_at`: `models.DateTimeField(auto_now_add=True)`
- **Future API Resource**: `/api/farmers/` (Supports `GET`, `POST`, `PUT`, `PATCH`, `DELETE`).

#### Table 2: `attendance`
- **Current Schema**:
  ```sql
  CREATE TABLE attendance (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      farmer_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      check_in TEXT,
      check_out TEXT,
      total_hours REAL,
      location TEXT,
      FOREIGN KEY (farmer_id) REFERENCES farmers (id)
  );
  ```
- **Current Rows**: 1 record.
- **Relationships**: Foreign Key to `farmers(id)`.
- **Recommended Django Model**: `Attendance` in `apps.attendance.models`
  - `farmer`: `models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='attendances')`
  - `date`: `models.DateField(default=timezone.now)`
  - `check_in`: `models.TimeField(null=True, blank=True)`
  - `check_out`: `models.TimeField(null=True, blank=True)`
  - `total_hours`: `models.DecimalField(max_digits=5, decimal_places=2, default=0.00)`
  - `location`: `models.CharField(max_length=255, blank=True, null=True)`
  - `device_coordinates`: `models.CharField(max_length=100, blank=True, null=True)`
- **Future API Resources**: `/api/attendance/check-in/`, `/api/attendance/check-out/`, `/api/attendance/logs/`, `/api/attendance/reports/`.

#### Table 3: `tasks`
- **Current Schema**:
  ```sql
  CREATE TABLE tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_name TEXT NOT NULL,
      assigned_to INTEGER,
      status TEXT NOT NULL,
      date TEXT NOT NULL,
      FOREIGN KEY (assigned_to) REFERENCES farmers (id)
  );
  ```
- **Current Rows**: 1 record.
- **Relationships**: Foreign Key to `farmers(id)`.
- **Recommended Django Model**: `Task` in `apps.tasks.models`
  - `task_name`: `models.CharField(max_length=255)`
  - `assigned_to`: `models.ForeignKey(Farmer, on_delete=models.SET_NULL, null=True, related_name='tasks')`
  - `status`: `models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')`
  - `date`: `models.DateField(auto_now_add=True)`
  - `completed_at`: `models.DateTimeField(null=True, blank=True)`
- **Future API Resource**: `/api/tasks/`, `/api/tasks/{id}/status/`.

#### Table 4: `animal_logs`
- **Current Schema**:
  ```sql
  CREATE TABLE animal_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      animal_type TEXT NOT NULL,
      confidence REAL,
      timestamp TEXT NOT NULL,
      field TEXT NOT NULL,
      image_path TEXT NOT NULL
  );
  ```
- **Current Rows**: 2 records.
- **Relationships**: Referenced by `alerts.animal_log_id`.
- **Recommended Django Model**: `AnimalDetectionLog` in `apps.detection.models`
  - `animal_type`: `models.CharField(max_length=100)`
  - `confidence`: `models.FloatField()`
  - `timestamp`: `models.DateTimeField(auto_now_add=True)`
  - `field_location`: `models.CharField(max_length=150, default='Main Field')`
  - `image`: `models.ImageField(upload_to='detections/%Y/%m/%d/')`
  - `threat_level`: `models.CharField(max_length=20, choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])`
- **Future API Resource**: `/api/detection/logs/`, `/api/detection/logs/{id}/`.

#### Table 5: `alerts`
- **Current Schema**:
  ```sql
  CREATE TABLE alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      animal_log_id INTEGER,
      alert_type TEXT NOT NULL,
      status TEXT NOT NULL,
      FOREIGN KEY (animal_log_id) REFERENCES animal_logs (id)
  );
  ```
- **Current Rows**: 2 records.
- **Relationships**: Foreign Key to `animal_logs(id)`.
- **Recommended Django Model**: `Alert` in `apps.alerts.models`
  - `detection_log`: `models.ForeignKey(AnimalDetectionLog, on_delete=models.CASCADE, related_name='alerts')`
  - `alert_type`: `models.CharField(max_length=50)` # e.g. Email + Buzzer, Email, Log Only
  - `status`: `models.CharField(max_length=30, default='Triggered')`
  - `triggered_at`: `models.DateTimeField(auto_now_add=True)`
  - `delivery_status`: `models.CharField(max_length=30, default='Sent')`
  - `error_message`: `models.TextField(blank=True, null=True)`
- **Future API Resource**: `/api/alerts/`, `/api/alerts/{id}/`.

---

## 7. AI and Computer Vision Audit

### 7.1 Framework & Weights
- **Framework**: `ultralytics` YOLOv8 Nano (`YOLO('yolov8n.pt')`).
- **Inference Runtime**: PyTorch (`torch`), NumPy, OpenCV (`cv2`).
- **Weight Location**: `yolov8n.pt` at project root (~6.55 MB).
- **Supported Animal Classes**: 29 classes defined in `modules/animal_detection.py`:
  `cat`, `dog`, `horse`, `sheep`, `cow`, `elephant`, `bear`, `zebra`, `giraffe`, `lion`, `tiger`, `cheetah`, `monkey`, `leopard`, `wolf`, `fox`, `deer`, `hippo`, `hyena`, `jackal`, `kangaroo`, `squirrel`, `penguin`, `eagle`, `owl`, `snake`, `crocodile`, `mouse`, `rat`.

### 7.2 Detection & Threat Classification Pipeline
```text
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Frame Capture  │ ──► │ YOLO Inference │ ──► │ Filter Animals │
│ (cv2.VideoCap) │     │ (yolov8n.pt)   │     │ (Conf > 0.50)  │
└────────────────┘     └────────────────┘     └────────────────┘
                                                       │
                                                       ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Trigger Alerts │ ◄── │ Cooldown Check │ ◄── │ Threat Scoring │
│ (Email/Buzzer) │     │ (dt >= 300s)   │     │ (High/Med/Low) │
└────────────────┘     └────────────────┘     └────────────────┘
        │
        ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Save Snapshot  │ ──► │ Save DB Record │ ──► │ Draw Bounding  │
│ (JPEG file)    │     │ (animal_logs)  │     │ Boxes on Frame │
└────────────────┘     └────────────────┘     └────────────────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │ MJPEG Stream   │
                                              │ (/video_feed)  │
                                              └────────────────┘
```

### 7.3 Identified Flaws & Migration Strategy
1. **Global Import Instantiation**: `VIDEO_STREAM = VideoStreaming(...)` runs on import in `app.py`. Under multi-worker servers (Gunicorn/Uvicorn), multiple processes will attempt to open webcam index `0`, causing device locking errors.
   - *Fix*: Encapsulate camera management into a thread-safe Singleton Service in `backend/services/camera/` that lazily acquires hardware access.
2. **Synchronous Execution of Alert Side-Effects**: `trigger_alert()` is called synchronously inside `detect_animals()`. When an animal is detected, the video thread blocks for 2 to 5 seconds while establishing an SMTP connection and transmitting the MIME payload, freezing the live stream.
   - *Fix*: Decouple alert generation from frame inference using asynchronous background tasks (threading queue, Celery, or Django background tasks).
3. **Hard-Coded Snapshot Path**: Saves images to `static/detected_<animal>_<time>.jpg`.
   - *Fix*: Standardize media storage using Django `settings.MEDIA_ROOT` and `ImageField`.

---

## 8. Alert and Notification Audit

### 8.1 Email Notification Mechanism
- **Engine**: Python standard library `smtplib` + `email.mime` (Multipart, Text, Image, Base64 Audio).
- **Host / Port**: `smtp.gmail.com:587` with `STARTTLS`.
- **Recipient Handling**: Parses comma-separated recipient strings from configuration.
- **Attachments**: Attaches detected animal snapshot JPEG and base64-encoded `warning_sound.mp3`.
- **Attendance Emails**: Dispatches personalized check-in and check-out confirmation emails to farmers containing timestamp, recorded location, and total hours.

### 8.2 Audio Buzzer Mechanism
- **Engine**: `pygame.mixer` (`pygame.mixer.Sound.play()`).
- **Sound Source**: `warning_sound.mp3` at root directory.
- **Trigger Rule**: Triggered only for `high` threat level detections.
- **Deployment Risk**: In headless Linux server environments (e.g. AWS EC2, DigitalOcean, Docker), `pygame` audio initialization will fail without a physical sound device/ALSA bridge.
   - *Fix*: Wrap buzzer execution in an environment-aware exception handler with an explicit setting to enable/disable physical buzzer playback or dispatch a WebSocket alert event to the frontend for browser-side audio playback.

### 8.3 Security Finding on Credentials
- **Finding**: Hard-coded SMTP sender credentials exist in `app.py`.
- **Classification**: **CRITICAL SECURITY RISK**.
- **Migration Strategy**: Remove hard-coded credentials immediately during Step 1. In Step 5 (`settings_app`), introduce database-backed email settings for non-sensitive data (SMTP host, port, sender email, recipient lists) and environment variables (`.env`) for SMTP passwords. The API must **never** return raw passwords in response payloads (return `has_password: true` boolean indicator only).

---

## 9. Authentication and API Security Audit

### 9.1 Current State
- **User Models**: None.
- **Authentication**: None.
- **Sessions / Tokens**: None.
- **Authorization**: None.
- **CSRF Protection**: Disabled / Absent.
- **CORS Configuration**: None (Single-origin Flask server).

### 9.2 Target Django REST Authentication Architecture
To support complete frontend decoupling and allow future replacement with modern SPAs or Lovable AI frontends:
1. **Authentication Protocol**: JSON Web Tokens (JWT) using `djangorestframework-simplejwt`.
   - `POST /api/auth/token/` (Login -> returns access token & refresh token).
   - `POST /api/auth/token/refresh/` (Token refresh).
   - `POST /api/auth/token/verify/` (Token verification).
2. **Role-Based Access Control (RBAC)**:
   - **Role: `Admin` / `FarmManager`**: Full read/write access to all endpoints (Settings, Hardware/Camera Controls, Farmer Management, Attendance Management, Task Assignment, Alert Management).
   - **Role: `FieldWorker` / `Viewer`**: Read-only access to camera feeds, self-attendance check-in/out, and viewing assigned tasks.
3. **CORS Security**: Use `django-cors-headers` to strictly allow designated frontend origins (e.g., `http://localhost:5173`, `http://localhost:3000`, staging domain) with credentials allowed.

---

## 10. Dependency Audit

| Dependency in `requirements.txt` | Installed Version | Current Purpose | Layer | Required After Migration? | Replacement / Migration Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Flask` | `>=2.3.2` | Web routing & template rendering | Backend Controller | **NO** | Replace with `Django>=4.2,<5.1` |
| `Flask-Bootstrap` | `==3.3.7.1` | Bootstrap 3 Jinja helpers | Frontend Helper | **NO** | Remove completely |
| `flask-bootstrap5` | Unpinned | Bootstrap 5 Jinja helpers | Frontend Helper | **NO** | Remove completely |
| `numpy` | `==1.26.4` | Frame manipulation & random colors | Backend AI | **YES** | Keep for OpenCV & YOLO array handling |
| `opencv-python` | `>=4.8.0` | Camera capture & image encoding | Backend CV | **YES** | Keep for camera capture service |
| `requests` | `==2.31.0` | HTTP client | Backend Utility | **REVIEW** | Keep if external webhooks are used |
| `torch` | `>=2.11.0` | Deep learning backend for YOLO | Backend AI | **YES** | Keep for YOLOv8 PyTorch model inference |
| `torchvision` | `>=0.26.0` | Computer vision PyTorch package | Backend AI | **YES** | Keep for vision processing pipeline |
| `ultralytics` | `>=8.0.0` | YOLOv8 object detection engine | Backend AI | **YES** | Keep for animal detection service |
| `pygame` | `>=2.6.1` | Local audio buzzer playback | Backend Audio | **REVIEW** | Retain for local buzzer; wrap with headless checks |
| `setuptools` | `>=70.0.0,<82.0.0`| Packaging tools | Build Tool | **YES** | Retain |
| `Pillow` | `>=12.0.0` | Image processing | Backend CV | **YES** | Keep for Django `ImageField` support |
| `matplotlib` | `>=3.8.0` | Plotting / visualization | Utility | **REVIEW** | Optional (Used internally by ultralytics) |

### Required New Backend Dependencies for Django Target
- `django>=4.2,<5.1` (Core framework)
- `djangorestframework>=3.14.0` (REST API engine)
- `django-cors-headers>=4.3.0` (Cross-Origin Resource Sharing)
- `djangorestframework-simplejwt>=5.3.0` (JWT Authentication)
- `python-dotenv>=1.0.0` (Environment variable configuration)
- `drf-spectacular>=0.27.0` (OpenAPI 3.0 / Swagger schema documentation)

---

## 11. Migration Risk Analysis

| Risk ID | Risk Description | Severity | Location | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | Hardcoded SMTP Credentials in Codebase | **CRITICAL** | `app.py:19-25` | Security breach if repo is shared | Migrate secrets to `.env` & DB; sanitize all reports |
| **RSK-02** | Blocking SMTP Calls in Video Frame Loop | **HIGH** | `animal_detection.py:90`, `alerts.py:23` | Frame stream freezes for 3-5s during alerts | Asynchronous alert worker / background threading |
| **RSK-03** | Multi-Worker Hardware Camera Contention | **HIGH** | `animal_detection.py:98`, `app.py:27` | Gunicorn forks crash trying to open webcam index 0 | Thread-safe Singleton Camera Service with lazy lock |
| **RSK-04** | Pygame Crash in Headless Linux Server | **HIGH** | `alerts.py:66` | Server crashes when trying to play sound without audio sink | Surround with headless detection & graceful bypass |
| **RSK-05** | Complete Absence of Auth & RBAC | **HIGH** | Entire application | Unauthorized access to camera feeds, data modification | Implement JWT auth & DRF permission classes |
| **RSK-06** | Direct Raw SQL Injection & Maintenance Risks | **MEDIUM** | `database/db.py`, `app.py` | Potential SQL injection, lack of schema migrations | Migrate entirely to Django ORM models & migrations |
| **RSK-07** | Frontend Tightly Coupled via Jinja2 | **HIGH** | `templates/*.html` | Inability to replace frontend with Lovable/SPA | Build complete REST API contract before frontend migration |
| **RSK-08** | Unmanaged Static Media Snapshot Dump | **MEDIUM** | `animal_detection.py:77` | Unbounded disk consumption in `static/` | Django `MEDIA_ROOT` with automated retention cleanup |
| **RSK-09** | Missing CORS Policy on API Endpoints | **MEDIUM** | Network boundary | Decoupled frontend blocked by browser CORS policy | Add `django-cors-headers` with environment-controlled origins |
| **RSK-10** | Missing Dynamic Settings UI/APIs | **MEDIUM** | `config.json` | Requires server code edit to change thresholds/emails | Build `settings_app` with full DRF CRUD endpoints |
| **RSK-11** | Hardcoded Detection Parameters | **LOW** | `animal_detection.py:53,35` | Inflexible confidence threshold and cooldown | Connect parameters to dynamic `settings_app` models |
| **RSK-12** | Dead JavaScript in Static Assets | **LOW** | `static/script.js` | Developer confusion, unused endpoint calls | Deprecate legacy script; replace with typed API services |

---

## 12. Recommended Migration Order

To guarantee zero regression, continuous system verification, and clean architectural separation, the migration must proceed in the following 20-step sequence:

```text
STEP 0  ──► STEP 1  ──► STEP 2  ──► STEP 3  ──► STEP 4  ──► STEP 5
Audit       Structure   Django+DRF  Models/ORM  Auth/JWT    Settings
  │
  ▼
STEP 6  ──► STEP 7  ──► STEP 8  ──► STEP 9  ──► STEP 10 ──► STEP 11
Dashboard   Farmers     Tasks       Attendance  YOLO Svc    Camera API
  │
  ▼
STEP 12 ──► STEP 13 ──► STEP 14 ──► STEP 15 ──► STEP 16 ──► STEP 17-19
History     Alerts      Audit Integ Frontend    Decoupling  Testing/Docs
```

1. **STEP 0**: Comprehensive Audit & Architecture Assessment (**THIS STEP - Analysis Only**).
2. **STEP 1**: Create Clean Separated Directory Structure (`backend/`, `frontend/`, `docs/`).
3. **STEP 2**: Django + Django REST Framework Project Initialization (`backend/config`).
4. **STEP 3**: Database Architecture Migration (Django ORM Models & Migrations for Farmers, Attendance, Tasks, Logs, Alerts).
5. **STEP 4**: Authentication & Authorization Layer (JWT, User Accounts, RBAC Permissions).
6. **STEP 5**: Dynamic Settings Module APIs (`apps/settings_app` - General, Senders, Receivers, Threat Rules).
7. **STEP 6**: Dashboard & Analytics API (`apps/dashboard` - Stats, aggregates, charts).
8. **STEP 7**: Farmer Workforce Management APIs (`apps/farmers` - CRUD, field assignments).
9. **STEP 8**: Task Management APIs (`apps/tasks` - CRUD, status updates).
10. **STEP 9**: Attendance & Geolocation APIs (`apps/attendance` - Check-in/out, hours, reports).
11. **STEP 10**: YOLOv8 Detection Service Refactoring (`services/yolo` - Singleton, dynamic confidence/rules).
12. **STEP 11**: Camera Hardware & Streaming APIs (`services/camera`, `apps/detection` - MJPEG streaming).
13. **STEP 12**: Detection History & Media APIs (`apps/detection` - Image queries, pagination, filters).
14. **STEP 13**: Alert & Notification Services (`services/notifications`, `apps/alerts` - Non-blocking email & buzzer).
15. **STEP 14**: Settings-to-Services Runtime Integration Audit (Verify dynamic reloading across all services).
16. **STEP 15**: Frontend API Client Integration (Connect UI components to DRF endpoints).
17. **STEP 16**: Frontend Decoupling & Lovable AI Replacement Verification.
18. **STEP 17**: End-to-End Automated Testing & Security Hardening.
19. **STEP 18**: Final Production Integration & Packaging.
20. **STEP 19**: Comprehensive Documentation, OpenAPI/Swagger Export & Viva Defense Material.

---

## 13. Step 0 Completion Checklist

- [x] Full workspace directory inspection completed without modifying existing files.
- [x] All Python files, Flask routes, templates, CSS, JavaScript, database, and asset files cataloged.
- [x] Hardcoded credentials identified and cataloged safely without printing sensitive values.
- [x] Database entities, schema definitions, and row counts audited against Django ORM requirements.
- [x] AI (YOLOv8) and Computer Vision (OpenCV) pipelines documented with concurrency bottlenecks flagged.
- [x] Alert subsystems (SMTP emails, pygame buzzer) analyzed and asynchronous refactoring designed.
- [x] 12 migration risks evaluated with clear mitigation strategies.
- [x] 20-step migration sequence formulated and validated.
- [x] 3 audit deliverables generated: `migration_audit.md`, `api_contract.md`, `architecture_assessment.md`.
- [x] Strict Rule Enforced: No Django code created, no files moved/renamed/deleted, no dependencies installed.

---

## 14. STEP 0 HANDOFF TO REVIEWER

### Confirmed Implemented Features
1. Real-time Live Camera Video Streaming (OpenCV webcam capture).
2. Live YOLOv8 Nano Object Detection with bounding box annotation.
3. 29 Animal Class filtering with 46-animal threat level evaluation (`high`, `medium`, `low`).
4. Automated snapshot image generation (`.jpg`) on animal detection.
5. Detection event logging to SQLite database (`animal_logs` table).
6. 5-minute alert cooldown timer (`notification_cooldown = 300`).
7. Automated SMTP email alerts with detected image and sound attachment for medium/high threats.
8. Automated local sound buzzer playback via `pygame` for high threats.
9. Farmer workforce registration and deletion (`farmers` table).
10. Attendance check-in and check-out with automatic total working hours computation.
11. Geolocation coordinate capture via HTML5 browser API and Google Maps linking in reports.
12. Automated attendance email notifications dispatched to farmers.
13. Task creation, worker assignment, and status completion tracking (`tasks` table).
14. Dashboard aggregate statistics cards (total farmers, today's attendance, alerts today, completed tasks).
15. Light-mode green glassmorphism CSS design system.

### Partially Implemented Features
1. **Dynamic Configuration**: `config.json` is loaded statically on startup; no runtime API or UI exists to modify settings.
2. **Camera Controls**: Simple toggle endpoints exist (`/toggle_camera`, `/toggle_detection`), but lack resolution/framerate configuration and thread safety.

### Not Found (Missing Features)
1. User Authentication (Login, Logout, Session tokens, Password management).
2. User Role-Based Access Control (Admin vs Field Worker permissions).
3. User Account / Profile Management.
4. Database-backed dynamic Email Sender / SMTP configuration.
5. Dynamic Alert Recipient management UI/API.
6. Asynchronous task queue for email and alert dispatch.
7. RESTful JSON API layer for workforce, tasks, and detections.

### Current Architecture Status
**HIGHLY COUPLED** (Monolithic Flask, Jinja2 template rendering, embedded SQL, synchronous background tasks).

### Frontend Replacement Readiness
**NOT READY** (Frontend is currently reliant on Jinja2 server-side rendering and HTML form POST redirects; migration to REST API in Steps 1–14 is required).

### Critical Migration Blockers
- None that prevent moving to Step 1. (All dependencies, schemas, and logic are fully understood and mapped).

### Questions Requiring Reviewer Decision
1. **JWT vs Session Auth**: Confirm SimpleJWT as the standard token authentication for the headless API (Recommended: **SimpleJWT**).
2. **Audio Buzzer in Server Deployment**: Confirm whether physical buzzer playback should be optional via a setting for headless cloud deployments (Recommended: **Yes, make buzzer optional via settings_app**).

### Recommended Status
👉 **READY FOR STEP 1** (Proceed with directory structure setup upon reviewer approval).
