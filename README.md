# FarmSync – Smart Farm Monitoring & Intelligent Animal Detection

**Architecture**: Decoupled API-First Django REST Backend & Independent Frontend  
**Migration Stage**: STEP 1 – Project Foundation & Directory Structure  
**Migration Status**: **Foundation Created. Business modules are migrated step by step.**  

---

## 1. Project Purpose & Overview

**FarmSync** is an intelligent farm monitoring and workforce management system. It combines Computer Vision (YOLOv8 + OpenCV) for real-time hazardous animal detection and automated alerting with smart workforce operations (farmer registration, geolocation-tagged attendance logging, and task assignment).

---

## 2. Why the Project is Being Migrated

The original prototype was built as a monolithic Flask application where HTML rendering (Jinja2), camera video capture, deep learning inference, raw database queries, and blocking SMTP alert calls were tightly entangled within a single synchronous Python process.

### Goals of the Migration:
1. **API-First Architecture**: Replace server-rendered HTML templates with clean, documented JSON REST API endpoints.
2. **Frontend-Backend Decoupling**: Completely isolate the frontend from backend business logic, enabling future frontend replacements (such as Lovable AI-generated interfaces or modern React/Vue SPAs) without altering backend Python code.
3. **Robust Data Layer**: Migrate from raw SQLite queries to structured Django ORM models with database migrations and validation.
4. **Asynchronous Services**: Isolate camera streaming, YOLOv8 inference, and notification dispatch into dedicated non-blocking service engines.
5. **Security & RBAC**: Introduce JSON Web Token (JWT) authentication, Role-Based Access Control, and dynamic secret management.

---

## 3. High-Level Architecture

The project is organized into clear architectural layers:

```text
AnimalDetection-Django/
│
├── backend/            # Django REST Framework API-First Backend
│   ├── config/         # Django Settings & Global URL Routing
│   ├── apps/           # Modular Domain Apps (Accounts, Farmers, Tasks, etc.)
│   ├── services/       # Isolated Engines (YOLO, Camera, Notifications)
│   ├── media/          # Managed Snapshot & Audio Storage
│   └── manage.py       # Django Management CLI
│
├── frontend/           # Decoupled Frontend Application (SPA / Lovable Ready)
│   └── README.md       # Frontend Architecture & Decoupling Guidelines
│
├── docs/               # System Documentation & Specifications
│   ├── migration/      # Step-by-Step Audit & Migration Reports
│   ├── api/            # REST API Contracts & Endpoint Schemas
│   └── architecture/   # System Architecture Assessments & Diagrams
│
├── legacy/             # Untouched Legacy Flask Codebase (Read-Only Reference)
│   └── README.md       # Legacy Reference Documentation
│
├── .gitignore          # Repository Git Ignore Rules
└── README.md           # Master Project Documentation
```

---

## 4. Directory Responsibilities

- **`backend/`**: Contains the Django project, Django REST Framework endpoints, database models, and service engines. The backend enforces all authorization, data validation, YOLO inference, and alert delivery.
- **`frontend/`**: The independent client presentation layer. Communicates with the backend exclusively via REST APIs (`/api/...`) and multipart MJPEG video streams. Contains zero direct database access.
- **`legacy/`**: Preserves the original Flask prototype as an untouched reference point for behavior verification during migration.
- **`docs/`**: Central repository for migration audit logs, OpenAPI-compatible API contracts, and architectural blueprints.

---

## 5. Explicit Decoupling Principle

> **Crucial Rule**: The frontend and backend are intentionally decoupled. The backend does not depend on Django HTML templates, a specific JavaScript framework, or the legacy frontend. Replacing or modifying the frontend client does not require rewriting backend logic.

---

## 6. How to Start the Django Backend

### Prerequisites
- Python 3.11+
- Virtual environment activated

### Setup & Run Commands
```bash
# 1. Navigate to backend directory
cd backend

# 2. Configure environment variables
cp .env.example .env

# 3. Install foundation dependencies
pip install -r requirements.txt

# 4. Verify system configuration
python manage.py check

# 5. Start the development server
python manage.py runserver 0.0.0.0:8000
```

---

## 7. Migration Roadmap

```text
[x] STEP 0: System Audit & Architecture Assessment
[x] STEP 1: Foundation & Separated Directory Structure (COMPLETED)
[ ] STEP 2: Django + DRF Base Project Initialization
[ ] STEP 3: Database Models & ORM Schema Migration
[ ] STEP 4: Authentication & JWT Authorization Layer
[ ] STEP 5: Dynamic Settings Module APIs
[ ] STEP 6: Dashboard & Analytics APIs
[ ] STEP 7: Farmer Workforce Management APIs
[ ] STEP 8: Task Delegation & Management APIs
[ ] STEP 9: Attendance & Geolocation APIs
[ ] STEP 10: YOLOv8 Detection Service Refactoring
[ ] STEP 11: Camera Hardware & MJPEG Streaming APIs
[ ] STEP 12: Detection History & Media APIs
[ ] STEP 13: Alert & Notification Background Services
[ ] STEP 14: Settings Runtime Integration Audit
[ ] STEP 15: Frontend API Client Integration
[ ] STEP 16: Lovable AI Replacement Verification
[ ] STEP 17: End-to-End Automated Testing & Security
[ ] STEP 18: Final Production Packaging
[ ] STEP 19: Final Documentation & Viva Preparation
```
