# FarmSync System Architecture Assessment

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 0 – Audit & Architecture Assessment  
**Date**: August 2026  
**Auditor**: Antigravity AI – Advanced Agentic Coding Assistant  
**Status**: ANALYSIS & ARCHITECTURAL BLUEPRINT  

---

## 1. Current Architecture Overview & Text Diagram

The existing application is structured as a single monolithic Python Flask process where presentation, application logic, hardware camera operations, deep learning inference, and database access are tightly bound together.

### Current Monolithic Flask Architecture Diagram
```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           CURRENT FLASK MONOLITHIC SYSTEM                         │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  [ Web Browser (User Interface) ]                                                 │
│        │                                                                          │
│        │  HTTP GET / HTML Form POST / Fetch (Mixed)                               │
│        ▼                                                                          │
│  [ Flask Web Server (app.py) ] ────────────────────────────────────────┐          │
│        │                                                               │          │
│        ├──► Jinja2 Template Engine (templates/*.html)                  │          │
│        │      - Embedded Python variables (`total_farmers`, etc.)      │          │
│        │      - Direct Jinja loops and conditional logic               │          │
│        │      - Form redirects via url_for()                           │          │
│        │                                                               │          │
│        ├──► Direct SQLite Layer (database/db.py)                       │          │
│        │      - Raw SQL strings with manual execution                  │          │
│        │      - Single SQLite file (`data.db`)                         │          │
│        │                                                               │          │
│        ├──► Video Streaming Controller (modules/animal_detection.py)   │          │
│        │      - Global OpenCV VideoCapture(0) capture instance         │          │
│        │      - Synchronous frame generator loop                       │          │
│        │                                                               │          │
│        ├──► AI Inference (ultralytics YOLOv8 Nano)                     │          │
│        │      - PyTorch model (`yolov8n.pt`)                           │          │
│        │      - Bounding box rendering directly onto frame             │          │
│        │      - Local JPEG file write to `static/detected_*.jpg`       │          │
│        │                                                               │          │
│        └──► Alert & Notification Subsystem (modules/alerts.py)         │          │
│               - Synchronous smtplib.SMTP connection (Blocks Stream)    │          │
│               - Hard-coded email credentials                           │          │
│               - Local pygame.mixer audio buzzer execution              │          │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Current Frontend / Backend Coupling Analysis

The current codebase is classified as **HIGHLY COUPLED**. The following architectural entanglements prevent the frontend from being cleanly separated or replaced:

| Coupling Point | Existing Code Location | Why It Prevents Frontend Replacement | Recommended Decoupling Strategy |
| :--- | :--- | :--- | :--- |
| **Jinja2 Server Rendering** | `app.py:41,55,61,66,137,143`, `templates/*.html` | HTML markup is generated on the server using Python objects and Jinja tags (`{{ total_farmers }}`, `{% for f in farmers %}`). A decoupled frontend (e.g. React or Lovable) cannot consume Jinja templates. | Convert all Flask view functions into Django REST Framework API endpoints that return pure JSON data. |
| **HTML Form POST Redirects** | `templates/farmers.html:38`, `attendance.html:35`, `tasks.html:35` | Forms submit standard `multipart/form-data` or `application/x-www-form-urlencoded` POST requests and expect HTTP 302 redirects. | Replace standard form actions with asynchronous JavaScript `fetch()` or Axios calls sending JSON to `/api/farmers/`, `/api/attendance/check-in/`, etc. |
| **Direct Route Generation via `url_for()`** | `templates/*.html:8,14,35` | Templates rely on Flask internal routing (`{{ url_for('static', filename='style.css') }}`). | Modern frontend assets are bundled independently via Vite/Webpack; API endpoints use static, documented URL paths (`/api/...`). |
| **Synchronous Alert Side-Effects in Video Stream** | `modules/animal_detection.py:90`, `modules/alerts.py:18` | When an animal is detected, the video streaming thread stops to connect to the SMTP server and send emails, causing the frontend video feed to freeze. | Offload all email dispatch and buzzer operations to asynchronous background workers / threads. |
| **Embedded SQL in Route Handlers** | `app.py:32,35,37,39,124,152` | Database queries are written directly inside Flask route definitions without data validation or serialization layers. | Encapsulate database interactions within Django ORM models and DRF ModelSerializers. |
| **Static File Image Serving from `static/`** | `modules/animal_detection.py:77`, `alerts.html:49` | Detected images are saved into the frontend static directory rather than a managed backend media storage. | Route all file uploads and snapshots through Django `settings.MEDIA_ROOT` and serve them via standard media URLs (`/media/detections/...`). |

---

## 3. Target Architecture Overview & Text Diagram

The target architecture enforces a strict **API-First separation** between the Django REST backend and the independent frontend client.

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                            TARGET DECOUPLED ARCHITECTURE                          │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   [ Independent Frontend Client (SPA / Lovable AI / React / Vue) ]                │
│   ├── Component-Driven UI (Dashboard, Workforce, Attendance, Stream, Tasks)       │
│   ├── Client-Side State & Routing                                                 │
│   ├── JWT Token Storage & HTTP Interceptors                                       │
│   └── Vanilla CSS / Green Glassmorphism Design System                             │
│                                                                                   │
│         ▲                                   ▲                                     │
│         │ JSON REST API (HTTP Bearer Auth)  │ Multipart MJPEG Video Stream        │
│         ▼                                   ▼                                     │
│                                                                                   │
│   [ Django REST Framework Backend (/backend) ]                                    │
│   ├── API Gateway & Router (config/urls.py)                                       │
│   ├── JWT Authentication & RBAC Middleware                                        │
│   ├── Domain Apps (/backend/apps/)                                                │
│   │     ├── accounts/     (User Auth, Profiles, RBAC)                             │
│   │     ├── core/         (Base Models, Exception Handlers)                       │
│   │     ├── settings_app/ (Dynamic Runtime Configuration)                         │
│   │     ├── dashboard/    (Analytics & Aggregate Stats)                           │
│   │     ├── farmers/      (Workforce Management)                                  │
│   │     ├── attendance/   (Check-In/Out & Geolocation)                            │
│   │     ├── tasks/        (Task Delegation & Status)                              │
│   │     ├── detection/    (Detection Logs & Image Queries)                        │
│   │     └── alerts/       (Alert Event History)                                   │
│   │                                                                               │
│   ├── Backend Core Engines (/backend/services/)                                   │
│   │     ├── yolo/         (YOLOv8 Singleton, Inference Engine)                    │
│   │     ├── camera/       (Thread-safe Capture, Streaming Service)                │
│   │     └── notifications/(Non-blocking SMTP & Buzzer Worker)                     │
│   │                                                                               │
│   ├── Database: SQLite3 via Django ORM (Migratable to PostgreSQL)                 │
│   └── Media Storage: /backend/media/detections/                                   │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Proposed `/backend` Directory Structure

```text
FarmSync/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   ├── settings.py
│   │   └── urls.py
│   │
│   ├── apps/
│   │   ├── accounts/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── core/
│   │   │   ├── exceptions.py
│   │   │   ├── pagination.py
│   │   │   └── permissions.py
│   │   │
│   │   ├── settings_app/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── dashboard/
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── farmers/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── attendance/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── tasks/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   ├── detection/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   │
│   │   └── alerts/
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       └── urls.py
│   │
│   ├── services/
│   │   ├── yolo/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py
│   │   │   ├── weights/
│   │   │   │   └── yolov8n.pt
│   │   │   └── threat_evaluator.py
│   │   │
│   │   ├── camera/
│   │   │   ├── __init__.py
│   │   │   ├── capture_manager.py
│   │   │   └── stream_generator.py
│   │   │
│   │   └── notifications/
│   │       ├── __init__.py
│   │       ├── email_service.py
│   │       ├── buzzer_service.py
│   │       └── worker.py
│   │
│   └── media/
│       ├── audio/
│       │   └── warning_sound.mp3
│       └── detections/
│
├── frontend/
│   └── (Decoupled SPA / Lovable AI client application)
│
└── docs/
    ├── migration_audit.md
    ├── api_contract.md
    ├── architecture_assessment.md
    └── architecture/
```

---

## 5. Division of Responsibilities

### 5.1 Backend Responsibilities
1. **Data Persistence & ORM**: Database schema, relationship integrity, and migrations via Django ORM.
2. **Security & Access Control**: JWT token issuance, password hashing (PBKDF2/Argon2), and Role-Based Access Control (RBAC).
3. **Input Validation**: Strict validation on all incoming request data via DRF Serializers.
4. **Computer Vision & AI Inference**: YOLOv8 model lifecycle management, frame processing, bounding box rendering, and animal classification.
5. **Hardware Management**: Thread-safe capture from webcam index 0 and MJPEG stream encoding.
6. **Asynchronous Alerts**: Background SMTP email dispatch with attachments and host machine buzzer triggers.
7. **Dynamic Configuration**: Runtime settings persistence, secret masking, and dynamic threshold enforcement.

### 5.2 Frontend Responsibilities
1. **User Experience & Presentation**: Render UI components using the green glassmorphism design system.
2. **User Interaction**: Manage client-side routing, form inputs, modal dialogs, and button state transitions.
3. **API Consumption**: Make asynchronous HTTP requests to backend REST endpoints (`/api/...`) with JWT `Authorization` headers.
4. **Media Rendering**: Display live video feeds using `<img src="/api/detection/camera/stream/" />` and render snapshot galleries.
5. **Client-Side Geolocation**: Call browser `navigator.geolocation` APIs to obtain coordinates and send them to the check-in/out APIs.

---

## 6. Subsystem Architectures

### 6.1 AI / YOLO Detection Service Architecture (`services/yolo/`)
- **Pattern**: Lazy Singleton Service (`YOLODetectionService`).
- **Initialization**: Model weights (`yolov8n.pt`) are loaded once upon initial service request, not during module import.
- **Dynamic Configuration**: Reads confidence threshold and threat classification mapping directly from `settings_app` database cache.
- **Output**: Returns annotated frame and detection metadata list without executing synchronous network calls.

### 6.2 Camera & Streaming Architecture (`services/camera/`)
- **Pattern**: Threaded Capture Manager (`CameraManager`).
- **Concurrency Control**: Uses Python `threading.Lock` to ensure only one thread reads from OpenCV `VideoCapture(0)` at any given time.
- **Client Fan-Out**: Multiple HTTP clients subscribing to `/api/detection/camera/stream/` receive copies of the latest encoded JPEG frame from a shared buffer.
- **Graceful Shutdown**: Automatically releases camera hardware on server termination or when toggled off via API.

### 6.3 Notification & Alert Architecture (`services/notifications/`)
- **Pattern**: Asynchronous Background Queue Worker.
- **Decoupling**: When a high or medium threat is detected, an event payload is pushed to an in-memory queue or thread pool.
- **Execution**: The notification worker consumes the event, formats the MIME email, attaches the saved snapshot, and contacts the SMTP server in the background without causing frame drops in the live stream.
- **Headless Safety**: Buzzer service checks if an audio output device is present before invoking `pygame.mixer` to prevent crashes in headless cloud environments.

### 6.4 Settings Module Architecture (`apps/settings_app/`)
- **Storage**: Database tables with default fixture seeding from `config.json`.
- **Dynamic Reloading**: Changes made via `/api/settings/*` take effect immediately at runtime across all services without requiring a server reboot.
- **Secret Protection**: SMTP password fields are marked `write_only=True` in DRF serializers and return masked metadata (`has_password: true`).

---

## 7. Frontend Replacement Strategy (Lovable AI Readiness)

To allow the frontend to be developed, refactored, or replaced using Lovable AI or any other SPA tool without touching backend code:

1. **Strict API Contract Adherence**: All backend endpoints follow the contracts defined in `api_contract.md`.
2. **CORS Enabling**: Backend includes `django-cors-headers` allowing any modern frontend dev server (e.g. `localhost:5173`, `localhost:3000`) to communicate seamlessly with `localhost:8000`.
3. **Authentication Transparency**: Authentication uses standard Bearer JWT headers in all API calls.
4. **Self-Contained Frontend**: The frontend contains zero Python dependencies, zero Jinja templates, and zero direct SQL access.

---

## 8. Summary of Migration Risks & Recommended Mitigations

```text
┌──────────────────────────────┬────────────┬────────────────────────────────────────────────────────┐
│ Identified Risk              │ Severity   │ Mitigation Strategy                                    │
├──────────────────────────────┼────────────┼────────────────────────────────────────────────────────┤
│ Hardcoded SMTP Credentials   │ CRITICAL   │ Move secrets to .env and database write-only settings. │
│ Video Stream Frame Freezing  │ HIGH       │ Move SMTP calls and buzzer triggers to async worker.   │
│ Multi-worker Camera Locking  │ HIGH       │ Implement Singleton CameraManager with thread lock.    │
│ Pygame Headless Audio Crash  │ HIGH       │ Add try/except device checks and settings bypass.      │
│ Total Absence of Auth / RBAC │ HIGH       │ Implement JWT authentication and DRF permissions.      │
│ Jinja2 Frontend Coupling     │ HIGH       │ Migrate all views to pure DRF JSON REST endpoints.     │
│ Raw SQL Injection Potential  │ MEDIUM     │ Refactor all data queries to Django ORM.               │
└──────────────────────────────┴────────────┴────────────────────────────────────────────────────────┘
```

---

## 9. Final Architecture Recommendation

1. **Approve Target Architecture**: The modular Django + DRF backend structure with separate service engines (`yolo`, `camera`, `notifications`) and a decoupled frontend SPA is fully validated and ready for execution.
2. **Proceed to STEP 1**: Establish the isolated folder structure (`/backend`, `/frontend`, `/docs`) and initialize the Django backend foundation in STEP 2.
