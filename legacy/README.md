# Legacy Flask Application Reference

**Project**: FarmSync / Intelligent Animal Detection System  
**Role**: Untouched Legacy Codebase & Reference Archive  
**Status**: READ-ONLY / PRESERVED  

---

## Purpose of Legacy Reference

This directory and the existing root-level Flask files represent the original prototype implementation of the **FarmSync / Intelligent Animal Detection System**. 

During the controlled migration to a decoupled Django REST Framework backend and independent frontend:
1. **Zero Modification**: No legacy Flask source files (`app.py`, `database/db.py`, `modules/*.py`, `templates/*.html`, `static/*`, `config.json`, `data.db`) are modified or deleted.
2. **Behavioral Ground Truth**: The legacy codebase serves as the baseline for verifying business logic, YOLO bounding box operations, threat level evaluations, attendance hours calculations, and alert triggers.
3. **No Direct Import**: The new Django backend (`/backend/`) and decoupled frontend (`/frontend/`) do **not** import, reference, or execute files from the legacy Flask implementation.

---

## Legacy File Index

| File / Folder | Original Purpose | Migration Target |
| :--- | :--- | :--- |
| `app.py` | Flask monolith entry point & route handlers | `backend/config/urls.py` & `backend/apps/*/views.py` |
| `config.json` | 46-animal threat mappings & wage configs | `backend/apps/settings_app/` (DB models & fixtures) |
| `data.db` | Raw SQLite database file | `backend/data.db` (Managed by Django ORM) |
| `database/db.py` | Direct SQLite connection & raw SQL queries | Replaced by Django ORM models and migrations |
| `modules/alerts.py` | Email (`smtplib`) & buzzer (`pygame`) alerts | `backend/services/notifications/` & `backend/apps/alerts/` |
| `modules/animal_detection.py` | YOLOv8 detection & OpenCV streaming generator | `backend/services/yolo/` & `backend/services/camera/` |
| `modules/attendance.py` | Check-in/out logic & hours calculation | `backend/apps/attendance/` |
| `modules/tasks.py` | Task assignment & status updates | `backend/apps/tasks/` |
| `templates/*.html` | 7 Jinja2 HTML templates | Replaced by decoupled frontend SPA components |
| `static/style.css` | Light green glassmorphism CSS design system | `frontend/src/styles/style.css` |
| `static/script.js` | Legacy jQuery event handlers | Replaced by frontend API services |
| `warning_sound.mp3` | Local audio buzzer file | `backend/media/audio/warning_sound.mp3` |
| `yolov8n.pt` | YOLOv8 Nano PyTorch model weights | `backend/services/yolo/weights/yolov8n.pt` |

---

> **Note**: For complete architectural analysis and migration details, refer to `docs/migration/migration_audit.md` and `docs/architecture/architecture_assessment.md`.
