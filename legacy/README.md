# FarmSync Legacy Application Archive

**Project**: FarmSync / Intelligent Animal Detection System  
**Archive Layer**: Historical Pre-Migration Flask Artifacts & Original SQLite Database  
**Status**: ARCHIVED FOR MIGRATION PROVENANCE & VIVA EVIDENCE  

---

## 1. Purpose of this Archive

This directory houses the original monolithic Python Flask application, SQLite database (`data.db`), and Jinja2 templates before the architectural migration to a modern, decoupled **Django REST Framework (DRF) backend + Single-Page Application (SPA) frontend**.

> [!NOTE]
> This folder is **NOT part of the active production runtime**. It is preserved strictly to demonstrate architectural evolution, baseline data fidelity, and project/Viva review.

---

## 2. Directory Structure

```
legacy/
├── README.md                 # This provenance documentation
├── flask_app/
│   ├── app.py                # Legacy Flask HTTP server & video feed generator
│   ├── config.json           # Pre-migration alert & system configuration
│   ├── run.txt               # Original manual run instructions
│   ├── requirements.txt      # Legacy Flask-only dependencies
│   ├── modules/              # Original business logic modules
│   │   ├── alerts.py         # SMTP email sending & notification dispatch
│   │   ├── animal_detection.py# YOLO detection & OpenCV video capture
│   │   ├── attendance.py     # SQLite worker check-in/out queries
│   │   └── tasks.py          # SQLite task assignment queries
│   ├── database/             # Original database connection helper
│   │   └── db.py             # SQLite raw SQL connection helper
│   └── templates/            # Original Flask server-side Jinja templates
│       ├── alerts.html
│       ├── attendance.html
│       ├── attendance_report.html
│       ├── camera.html
│       ├── dashboard.html
│       ├── farmers.html
│       └── tasks.html
├── data/
│   └── data.db               # Original SQLite database with 6 tables
└── source_assets/
    └── layout.jpg            # Original UI wireframe diagram
```

---

## 3. Legacy vs. Active Architecture Mapping

| Legacy Flask / SQLite Component | Active Django / SPA Equivalent | Migration Status |
|---|---|---|
| `app.py` (Flask Routes) | `backend/config/urls.py` + `backend/apps/*/views.py` | Migrated to Version 1 REST API Gateway (`/api/v1/`) |
| `modules/animal_detection.py` | `backend/services/yolo/` + `backend/apps/detection/` | Migrated to Singleton Cached YOLOv8 Inference Engine |
| `modules/alerts.py` | `backend/apps/alerts/` + `backend/apps/settings_app/` | Migrated to Dynamic Alert Triggering & Settings |
| `modules/attendance.py` | `backend/apps/attendance/` | Migrated to Attendance REST API & ORM Models |
| `modules/tasks.py` | `backend/apps/tasks/` | Migrated to Tasks Management REST API |
| `database/db.py` & `data.db` | `backend/apps/*/models.py` & `backend/db.sqlite3` | Migrated to Django ORM Models with foreign keys |
| `templates/*.html` (Jinja) | `frontend/index.html` + `frontend/js/app.js` | Migrated to Decoupled Single-Page Application (SPA) |
| `config.json` | `apps.settings_app.models.ProjectSettings` | Migrated to Database-backed Runtime Settings Singleton |

---

## 4. Legacy Database Integrity Guarantee

- `legacy/data/data.db` is frozen in time as the initial historical data source.
- Django migrations and tests run exclusively against `backend/db.sqlite3` (or ephemeral in-memory test databases).
- No write operations are permitted against `legacy/data/data.db`.
