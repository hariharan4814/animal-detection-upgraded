# FarmSync Project Settings & Configuration Management REST API Specification (Step 12)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 12 – Project Settings & Configuration Management REST API  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Architectural Summary & Scope

The **Settings Module** (`apps.settings_app`) provides a secure, unified configuration management API for FarmSync. It exposes the global `ProjectSettings` singleton as well as auxiliary email dispatch and receiver configurations.

### Key Architectural Decisions:
1. **Singleton Configuration Source of Truth**: Reuses `ProjectSettings.get_settings()` (`apps.settings_app.models.ProjectSettings`) as the global source of truth for all runtime operational parameters, including YOLO detection thresholds, cooldown durations, audio/email toggles, and work shift schedules.
2. **Zero New Migrations & Model Reuse**: Operates on the existing `ProjectSettings` model without creating duplicate models or schema alterations (`python manage.py makemigrations --check` -> "No changes detected").
3. **Seamless Step 10 Detection Integration**: Any change made via `PATCH /api/v1/settings/` immediately alters detection behavior on subsequent frames and inference requests without requiring a server restart.
4. **Strict Security & Zero Secret Exposure**: Sensitive credentials (such as `smtp_password`, Django `SECRET_KEY`, JWT keys, and password hashes) are never exposed via API endpoints.
5. **Partial Updates (PATCH) & Immutability of Creation/Deletion**: Global configuration supports `PATCH` partial modifications. `POST` and `DELETE` return `HTTP 405 Method Not Allowed` to prevent creating duplicate configuration records or deleting system configuration.

---

## 2. Legacy Configuration Audit & Classification Matrix

| Configuration Field | Legacy Source | Existing Django Source | Classification |
|---|---|---|---|
| **work_start_time** | `config.json` line 2 (`"work_start_time": "08:00"`) | `ProjectSettings.work_start_time` (TimeField) | **LEGACY-DERIVED** |
| **wage_per_hour** | `config.json` line 3 (`"wage_per_hour": 15`) | `ProjectSettings.wage_per_hour` (FloatField) | **LEGACY-DERIVED** |
| **threat_level_overrides** | `config.json` lines 4-50 (`"animal_threat_levels": {...}`) | `ProjectSettings.threat_level_overrides` (JSONField) | **LEGACY-DERIVED** |
| **detection_confidence_threshold** | `modules/animal_detection.py` line 53 (`conf > 0.5`) | `ProjectSettings.detection_confidence_threshold` (FloatField, default 0.50) | **LEGACY-DERIVED** |
| **alert_cooldown_seconds** | `modules/animal_detection.py` line 35 (`notification_cooldown = 300`) | `ProjectSettings.alert_cooldown_seconds` (IntegerField, default 60) | **LEGACY-DERIVED** |
| **camera_device_index** | `modules/animal_detection.py` line 98 (`cv2.VideoCapture(0)`) | `ProjectSettings.camera_device_index` (IntegerField, default 0) | **LEGACY-DERIVED** |
| **system_name** | None (hardcoded in legacy UI) | `ProjectSettings.system_name` (CharField) | **NEW DJANGO ENHANCEMENT** |
| **detection_enabled** | `app.py` line 100 (`VIDEO_STREAM._detect`) | `ProjectSettings.detection_enabled` (BooleanField, default True) | **LEGACY-DERIVED & ENHANCED** |
| **audio_buzzer_enabled** | `modules/alerts.py` line 21 (`play_buzzer()`) | `ProjectSettings.audio_buzzer_enabled` (BooleanField, default True) | **LEGACY-DERIVED & ENHANCED** |
| **email_alerts_enabled** | `modules/alerts.py` line 17 (`send_email(...)`) | `ProjectSettings.email_alerts_enabled` (BooleanField, default True) | **LEGACY-DERIVED & ENHANCED** |
| **created_at / updated_at** | None | `ProjectSettings.created_at`, `updated_at` (DateTimeField) | **NEW DJANGO ENHANCEMENT** |

---

## 3. Endpoints Reference

Base path: `/api/v1/settings/`

| Method | Endpoint | Authorization | Description | Classification |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/settings/` | Authenticated | Retrieve active global `ProjectSettings` configuration. | **NEW DJANGO ENHANCEMENT** |
| `PATCH` | `/api/v1/settings/` | Staff / Admin | Partially update active global `ProjectSettings`. | **NEW DJANGO ENHANCEMENT** |
| `PUT` | `/api/v1/settings/` | Staff / Admin | Update active global `ProjectSettings`. | **NEW DJANGO ENHANCEMENT** |
| `POST` | `/api/v1/settings/` | — | Method Not Allowed (HTTP 405). Singleton configuration cannot be duplicated. | **SINGLETON SAFETY** |
| `DELETE` | `/api/v1/settings/` | — | Method Not Allowed (HTTP 405). Singleton configuration cannot be deleted. | **SINGLETON SAFETY** |
| `GET` | `/api/v1/settings/project/` | Authenticated | Legacy alias for retrieving global project settings. | **BACKWARD COMPATIBILITY** |
| `GET` | `/api/v1/settings/email-sender/` | Staff / Admin | Retrieve active SMTP sender configuration. | **NEW DJANGO ENHANCEMENT** |
| `PUT` | `/api/v1/settings/email-sender/` | Staff / Admin | Update active SMTP sender configuration (write-only password). | **NEW DJANGO ENHANCEMENT** |
| `GET` | `/api/v1/settings/receivers/` | Authenticated | List all alert notification recipients. | **NEW DJANGO ENHANCEMENT** |
| `POST` | `/api/v1/settings/receivers/` | Staff / Admin | Create a new alert recipient. | **NEW DJANGO ENHANCEMENT** |
| `GET` | `/api/v1/settings/receivers/{id}/` | Authenticated | Retrieve single alert recipient details. | **NEW DJANGO ENHANCEMENT** |
| `PUT` | `/api/v1/settings/receivers/{id}/` | Staff / Admin | Update single alert recipient details. | **NEW DJANGO ENHANCEMENT** |
| `DELETE` | `/api/v1/settings/receivers/{id}/` | Staff / Admin | Delete single alert recipient. | **NEW DJANGO ENHANCEMENT** |

---

## 4. Request & Response Examples

### 4.1 Retrieve Settings (`GET /api/v1/settings/`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Project settings retrieved successfully.",
    "data": {
      "id": 1,
      "system_name": "FarmSync Intelligent Monitoring",
      "alert_cooldown_seconds": 60,
      "detection_confidence_threshold": 0.5,
      "camera_device_index": 0,
      "work_start_time": "08:00:00",
      "wage_per_hour": 15.0,
      "detection_enabled": true,
      "audio_buzzer_enabled": true,
      "email_alerts_enabled": true,
      "threat_level_overrides": {
        "wolf": "high",
        "deer": "low"
      },
      "created_at": "2026-08-24T12:00:00Z",
      "updated_at": "2026-08-24T12:00:00Z"
    }
  }
  ```

---

### 4.2 Partially Update Settings (`PATCH /api/v1/settings/`)
- **Request**:
  ```json
  {
    "detection_confidence_threshold": 0.70,
    "alert_cooldown_seconds": 120,
    "threat_level_overrides": {
      "wolf": "high",
      "leopard": "high",
      "sheep": "low"
    }
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Project settings partially updated successfully.",
    "data": {
      "id": 1,
      "system_name": "FarmSync Intelligent Monitoring",
      "alert_cooldown_seconds": 120,
      "detection_confidence_threshold": 0.7,
      "camera_device_index": 0,
      "work_start_time": "08:00:00",
      "wage_per_hour": 15.0,
      "detection_enabled": true,
      "audio_buzzer_enabled": true,
      "email_alerts_enabled": true,
      "threat_level_overrides": {
        "wolf": "high",
        "leopard": "high",
        "sheep": "low"
      },
      "created_at": "2026-08-24T12:00:00Z",
      "updated_at": "2026-08-24T16:10:00Z"
    }
  }
  ```

---

## 5. Security & Server-Side Validation

1. **Authentication & Authorization**:
   - `GET /api/v1/settings/` requires standard user authentication (`HTTP 401 Unauthorized` when unauthenticated).
   - `PATCH /api/v1/settings/` is strictly restricted to staff and superusers (`HTTP 403 Forbidden` for non-staff users).
2. **Numeric & Choice Boundaries**:
   - `detection_confidence_threshold`: Enforced float between `0.01` and `1.00`.
   - `alert_cooldown_seconds`: Enforced non-negative integer (`>= 0`).
   - `camera_device_index`: Enforced non-negative integer (`>= 0`).
   - `wage_per_hour`: Enforced non-negative float (`>= 0.0`).
   - `threat_level_overrides`: Validated dictionary where each value must be one of `['high', 'medium', 'low']`.
3. **Data Protection**:
   - Zero exposure of passwords, password hashes, JWT secrets, or internal security keys.
