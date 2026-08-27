# Step 21 — Animal Threat Classification, Alert Evidence & Email Templates QA Plan & Test Log

**Author:** FarmSync System Engineer  
**Date:** 2026-08-26  
**Status:** PASS (159/159 Automated Backend Tests Passing, Frontend TypeScript Build Passing)

---

## 1. Test Scope & Objectives

Step 21 establishes a centralized, database-backed animal hazard threat classification system, custom dynamic email notification templates with Django template variable rendering, secure evidence download and authorized deletion, and multi-tier hazard alert dispatch (sirens, emails, informational logs).

---

## 2. Test Execution Matrix

| Test Domain | Target Endpoints / Services | Verification Methods | Result |
| :--- | :--- | :--- | :--- |
| **Threat Classification** | `services/threat_classification.py`, `AnimalThreatRule` | Multi-animal severity scoring, cache invalidation, fallback to MEDIUM, 3-tier hierarchy (HIGH=3, MEDIUM=2, LOW=1) | **PASS** |
| **Threat Rules REST API** | `GET/POST /api/v1/settings/threat-rules/`, `PUT/DELETE /api/v1/settings/threat-rules/<id>/`, `POST .../reset-defaults/` | Auto-seeding, filtering by `threat_level`, CRUD operations, staff permissions enforcement (403 for non-staff) | **PASS** |
| **Threat Email Templates** | `GET /api/v1/settings/email-templates/`, `PUT .../<threat_level>/`, `POST .../preview/`, `POST .../reset-defaults/` | Django syntax verification (syntax error returns 400), live sample preview rendering, factory defaults reset | **PASS** |
| **Notification Dispatch** | `NotificationService`, `Alert`, `ProjectSettings` | High threat audio siren + SMTP email dispatch, Medium threat email dispatch, Low threat logging, snapshot attachment | **PASS** |
| **Evidence Management** | `GET /api/v1/alerts/<id>/download/`, `DELETE /api/v1/alerts/<id>/` | Snapshot download with `Content-Disposition`, path-traversal prevention, staff-only deletion with unreferenced image cleanup | **PASS** |
| **Frontend UI/UX** | React Vite app routes (`settings`, `alerts`, `monitoring`, `detection-logs`, `dashboard`) | TypeScript compilation (`npm run build`), Lucide icons, responsive tables, preview modal, lightbox dialogs | **PASS** |

---

## 3. Automated Test Suite Results

```text
Ran 159 tests in 90.714s
OK
System check identified no issues (0 silenced).
```

### Verified Test Cases:
1. `AnimalThreatRule` and `ThreatEmailTemplate` database models and initial migrations (`alerts.0002`, `detection.0002`, `settings_app.0002`).
2. Centralized classification via `classify_animal(animal_name, confidence, custom_overrides)`.
3. Cooldown tracking per `(species, threat_tier)` tuple to prevent low-threat detections from suppressing critical high-threat sirens/alerts.
4. Security permission checks: regular worker users get HTTP 403 Forbidden when attempting to modify threat rules, templates, or delete alerts.
5. Email template preview generator renders dynamic variables `{{ animal_name }}`, `{{ threat_level }}`, `{{ confidence }}`, `{{ detected_at }}`, `{{ camera_name }}`, and `{{ alert_id }}`.
6. Evidence image downloading returns `image/jpeg` with attachment headers and prevents directory traversal attacks.

---

## 4. Frontend Verification Summary

- **Production Build:** Vite + TanStack Router bundle compiled cleanly into `.output/` with zero TypeScript compiler diagnostics.
- **Settings Page:** Added dedicated tabs for *Threat Rules* (table with active switches, level select, factory reset) and *Email Templates* (segmented tiers, context placeholder insertion chips, live preview modal, factory reset).
- **Alerts Center:** Added threat level filter buttons, evidence lightbox modal, safe snapshot download handler, and staff-authorized deletion confirmation dialog.
- **AI Monitoring:** Prominent High-Threat alert banner, multi-animal threat tier breakdown with individual confidence bars, and settings indicator for attached snapshot emails.
