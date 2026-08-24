# FarmSync Repository Cleanup & Legacy Archival Specification (Step 17)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 17 – Safe Repository Cleanup & Legacy Archival  
**Date**: August 2026  
**Status**: ACTIVE & FULLY VERIFIED  

---

## 1. Executive Summary

Step 17 executed the repository consolidation and legacy archival planned in Step 16.
All monolithic Flask files, Jinja templates, and original SQLite database were organized into a structured `legacy/` archive for academic review and migration provenance. Redundant root-level duplicates were pruned in favor of canonical specifications in `docs/`.

### Quality & Safety Validation:
- **Pre-Cleanup Test Baseline**: 189 / 189 passing tests.
- **Post-Cleanup Test Baseline**: **189 / 189 passing tests (100% PASS)**.
- **Django System Check (`python manage.py check`)**: PASSED (0 issues).
- **Migration Check (`python manage.py makemigrations --check`)**: PASSED (No changes detected).
- **Zero Business Logic Regressions**: All 9 Django apps, REST APIs, and the SPA frontend remain intact.
- **Legacy Database Protection**: `legacy/data/data.db` is archived read-only; zero migrations were executed against it.

---

## 2. Directory Transformation & Archival Structure

```
AnimalDetection-main/
├── backend/                  # Active Django REST API Backend (9 Apps + YOLO Engine)
├── frontend/                 # Active Decoupled Single-Page Application (HTML/JS/CSS)
├── docs/                     # Canonical System Documentation (api/, architecture/, migration/, qa/)
├── static/                   # Active UI brand & background image assets
├── legacy/                   # Complete Historical Archive (Preserved for Viva Evidence)
│   ├── README.md             # Provenance & architectural mapping documentation
│   ├── flask_app/            # Original Flask source, modules, database helpers, templates, config
│   │   ├── app.py
│   │   ├── config.json
│   │   ├── run.txt
│   │   ├── requirements.txt
│   │   ├── modules/
│   │   ├── database/
│   │   └── templates/
│   ├── data/
│   │   └── data.db           # Original SQLite database (6 tables)
│   └── source_assets/
│       └── layout.jpg        # Original UI layout diagram
├── yolov8n.pt                # YOLOv8 Nano weights file
├── warning_sound.mp3         # Hardware buzzer audio asset
├── README.md                 # Primary project documentation
├── LICENSE                   # Open-source MIT license
├── .gitignore                # Production ignore rules
└── STEP_*_REPORT.md (16 files)# Complete milestone verification audit trail
```

---

## 3. Documentation Consolidation Decisions

| Document | Action Taken | Rationale |
|---|---|---|
| `api_contract.md` (root) | **DELETED** | Canonical, authoritative copy maintained under `docs/api/api_contract.md`. |
| `architecture_assessment.md` (root) | **DELETED** | Canonical, authoritative copy maintained under `docs/architecture/architecture_assessment.md`. |
| `migration_audit.md` (root) | **DELETED** | Canonical, authoritative copy maintained under `docs/migration/migration_audit.md`. |
| `review1.txt` (root) | **DELETED** | Empty 0-byte orphan scratch file with zero references. |
| `requirements.txt` (root) | **ARCHIVED** | Moved to `legacy/flask_app/requirements.txt` as it specifies Flask dependencies only. Active backend uses `backend/requirements.txt`. |
