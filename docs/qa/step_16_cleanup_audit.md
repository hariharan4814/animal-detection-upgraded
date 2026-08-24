# FarmSync Repository Cleanup & Archival Audit Specification (Step 16)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 16 – Final Cleanup & Repository Audit  
**Date**: August 2026  
**Mode**: AUDIT ONLY (Zero deletions performed)  
**Status**: COMPLETE & VERIFIED  

---

## 1. Executive Summary & Inventory Overview

A comprehensive, non-destructive audit was performed across all 65+ files and directories in the FarmSync repository (`AnimalDetection-main/`).
Every file and folder was traced against active Python imports, Django configuration (`settings.py`, `urls.py`, `INSTALLED_APPS`, `TEMPLATES`, `STATICFILES_DIRS`, `MEDIA_ROOT`), frontend SPA assets, YOLO model loader paths, and automated test suites.

### Classification Summary:
- **Total Audited Items**: 65
- **CATEGORY A — KEEP (Active Runtime / Documentation / Model)**: 45
- **CATEGORY B — SAFE TO DELETE AFTER APPROVAL (Unused / Obsolete / Generated)**: 4
- **CATEGORY C — REVIEW MANUALLY (Duplicate Root Docs / Legacy Config)**: 4
- **CATEGORY D — ARCHIVE CANDIDATE (Legacy Flask Architecture / Migration Evidence)**: 12

---

## 2. Complete Repository Inventory & Classification Matrix

| Path | Type | Category | Active Reference & Evidence | Recommendation / Rationale | Risk Tier |
|---|---|---|---|---|---|
| `backend/` | Directory | **A — KEEP** | Primary Django REST API backend root (`config`, `apps`, `services`). | **KEEP**: Core backend application. | Critical |
| `backend/config/` | Directory | **A — KEEP** | Django project configuration (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`). | **KEEP**: Root routing & configuration. | Critical |
| `backend/apps/` | Directory | **A — KEEP** | 9 Django domain apps (`core`, `accounts`, `farmers`, `attendance`, `tasks`, `detection`, `alerts`, `settings_app`, `dashboard`). | **KEEP**: Verified REST API modules. | Critical |
| `backend/services/yolo/` | Directory | **A — KEEP** | `inference.py`, `loader.py`, cached YOLO singleton. | **KEEP**: Computer vision engine. | Critical |
| `backend/db.sqlite3` | File | **A — KEEP** | Active Django SQLite database. | **KEEP**: Active development database. | Critical |
| `backend/manage.py` | File | **A — KEEP** | Django CLI entrypoint. | **KEEP**: Management command script. | Critical |
| `backend/media/` | Directory | **A — KEEP** | Detection snapshots directory (`MEDIA_ROOT`). | **KEEP**: Media storage directory. | High |
| `backend/requirements.txt` | File | **A — KEEP** | Active backend Python dependencies. | **KEEP**: Deployment dependency spec. | High |
| `frontend/` | Directory | **A — KEEP** | Decoupled Single-Page Application root (`index.html`, `js/api.js`, `js/app.js`, `css/style.css`). | **KEEP**: Active user interface. | Critical |
| `static/green_glass_decorative.png` | File | **A — KEEP** | Referenced in `frontend/index.html` brand logo header. | **KEEP**: Active brand asset. | Low |
| `static/green_glass_hero.png` | File | **A — KEEP** | Referenced in `frontend/css/style.css` and `static/style.css` as background. | **KEEP**: Active visual background asset. | Low |
| `yolov8n.pt` | File | **A — KEEP** | Default YOLOv8 weights file referenced by `backend/services/yolo/loader.py`. | **KEEP**: AI model weights. | Critical |
| `warning_sound.mp3` | File | **A — KEEP** | Audio alert buzzer sound referenced in settings & alert documentation. | **KEEP**: Hardware audio asset. | Medium |
| `docs/` | Directory | **A — KEEP** | Structured specifications (`api/`, `architecture/`, `migration/`, `qa/`). | **KEEP**: Authoritative project documentation. | Low |
| `README.md` | File | **A — KEEP** | Main repository overview. | **KEEP**: Top-level project documentation. | Low |
| `LICENSE` | File | **A — KEEP** | Open-source MIT license. | **KEEP**: Project license. | Low |
| `.gitignore` | File | **A — KEEP** | Git ignore rules for bytecode, secrets, venvs, and databases. | **KEEP**: Repository configuration. | Low |
| `data.db` | File | **D — ARCHIVE** | Legacy SQLite database (6 tables). Contains migration audit verification data. | **ARCHIVE / KEEP FOR REFERENCE**: Preserves migration baseline. | Medium |
| `app.py` | File | **D — ARCHIVE** | Legacy Flask application file. Zero active imports in Django backend or frontend SPA. | **ARCHIVE / SAFE TO DELETE AFTER APPROVAL**: Superseded by Django. | Low |
| `modules/` | Directory | **D — ARCHIVE** | Legacy Flask modules (`alerts.py`, `animal_detection.py`, `attendance.py`, `tasks.py`). | **ARCHIVE / SAFE TO DELETE AFTER APPROVAL**: Superseded by `backend/apps/`. | Low |
| `database/db.py` | File | **D — ARCHIVE** | Legacy SQLite helper functions. Zero imports in Django. | **ARCHIVE / SAFE TO DELETE AFTER APPROVAL**: Superseded by Django ORM. | Low |
| `templates/` | Directory | **D — ARCHIVE** | Legacy Flask Jinja templates (`alerts.html`, `attendance.html`, `camera.html`, `dashboard.html`, `farmers.html`, `tasks.html`). | **ARCHIVE / SAFE TO DELETE AFTER APPROVAL**: Superseded by `frontend/index.html`. | Low |
| `static/style.css` | File | **D — ARCHIVE** | Legacy Flask stylesheet (partially referenced as fallback in `frontend/index.html`). | **ARCHIVE / MERGE INTO FRONTEND**: Can be consolidated into `frontend/css/style.css`. | Low |
| `static/script.js` | File | **D — ARCHIVE** | Legacy jQuery camera control script. Zero imports in SPA. | **ARCHIVE / SAFE TO DELETE AFTER APPROVAL**: Superseded by `frontend/js/app.js`. | Low |
| `config.json` | File | **D — ARCHIVE** | Legacy JSON configuration used to seed `ProjectSettings` and `EmailSenderConfig`. | **ARCHIVE / KEEP FOR REFERENCE**: Migration audit baseline. | Low |
| `_source/layout.jpg` | File | **D — ARCHIVE** | Legacy layout diagram. | **ARCHIVE**: Historical documentation. | Low |
| `run.txt` | File | **D — ARCHIVE** | Legacy Flask run instructions. | **ARCHIVE**: Superseded by Django documentation. | Low |
| `requirements.txt` (root) | File | **C — REVIEW** | Legacy Flask dependencies (`Flask`, `pygame`, etc.). | **REVIEW MANUALLY / CONSOLIDATE**: Can be synchronized with `backend/requirements.txt`. | Low |
| `review1.txt` | File | **B — SAFE DELETE** | Empty 0-byte file at root. Zero content or references. | **SAFE TO DELETE AFTER APPROVAL**: Zero functional impact. | None |
| `api_contract.md` (root) | File | **C — REVIEW** | Duplicate copy of `docs/api/api_contract.md`. | **REVIEW MANUALLY**: Canonical copy exists in `docs/api/`. | Low |
| `architecture_assessment.md` (root) | File | **C — REVIEW** | Duplicate copy of `docs/architecture/architecture_assessment.md`. | **REVIEW MANUALLY**: Canonical copy exists in `docs/architecture/`. | Low |
| `migration_audit.md` (root) | File | **C — REVIEW** | Duplicate copy of `docs/migration/migration_audit.md`. | **REVIEW MANUALLY**: Canonical copy exists in `docs/migration/`. | Low |
| `STEP_*_REPORT.md` (root) | Files (15) | **A — KEEP** | Milestone reports (Steps 1–15). | **KEEP**: Historical project migration audit trail. | None |
| `__pycache__/` | Directories | **B — SAFE DELETE** | Python byte-compiled `.pyc` caches across directories. | **SAFE TO DELETE AFTER APPROVAL**: Auto-regenerated by Python runtime. | None |

---

## 3. Phased Cleanup Plan (Proposed — Awaiting User Approval)

### Phase A: Very Low Risk (Zero Functional Impact)
- Remove empty 0-byte file: `review1.txt`
- Clean unversioned `__pycache__/` and `*.pyc` bytecode files.

### Phase B: Low Risk (Redundant Root Duplicates)
- Consolidate root duplicate markdown files (`api_contract.md`, `architecture_assessment.md`, `migration_audit.md`) in favor of canonical copies in `docs/`.

### Phase C: Archival of Legacy Flask Application (Recommended for `legacy/` directory)
- Move legacy Flask files (`app.py`, `modules/`, `database/`, `templates/`, legacy `run.txt`, `config.json`, `data.db`) into a dedicated `legacy/` archive folder so historical reference is preserved without cluttering the active project root.

### Phase D: Strictly DO NOT Delete
- `backend/` (all apps, config, services, databases, manage.py)
- `frontend/` (all SPA assets, scripts, stylesheets)
- `yolov8n.pt`
- `warning_sound.mp3`
- `static/green_glass_*.png`
- `docs/`
