# FarmSync Detection Engine & YOLO Computer Vision API Specification (Step 10)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 10 – Detection Engine & YOLO Computer Vision Service Migration  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Architectural Summary & Scope

The **Detection Engine & Computer Vision Subsystem** (`apps.detection` & `services.yolo`) provides AI-driven animal detection, threat level scoring, frame-level logging, alert dispatching, live MJPEG video streaming, and engine management.

### Key Architectural Decisions:
1. **Model Reuse & Zero New Migrations**: Reuses the existing `AnimalLog` model (`apps.detection.models.AnimalLog`) and `Alert` model (`apps.alerts.models.Alert`). No duplicate database models or schema migrations were created.
2. **Lazy Singleton Model Caching**: YOLOv8 weights (`yolov8n.pt`) are loaded lazily upon first inference and cached in memory via `services.yolo.loader.get_model()`, preventing expensive disk reads or memory re-allocations on every frame or request.
3. **Single Source of Truth Configuration**: Detection thresholds, device indices, master switches, and threat level overrides are dynamically read from `ProjectSettings` (`apps.settings_app.models.ProjectSettings`).
4. **Hardware-Independent Architecture**: Headless servers, Docker environments, and automated unit tests run with 100% reliability without requiring a physical webcam, GPU, or online weight downloads.
5. **Decoupled API Contract**: Conforms strictly to FarmSync's standardized JSON envelope (`success`, `message`, `data`/`errors`).

---

## 2. Legacy Evidence Audit & Classification Matrix

| Behavior | Verified | Exact Source | Classification |
|---|---|---|---|
| **YOLO Library** | YES | `modules/animal_detection.py` line 6 (`from ultralytics import YOLO`) | **LEGACY-DERIVED** |
| **Model Weights** | YES | `modules/animal_detection.py` line 26 (`yolov8n.pt` in root) | **LEGACY-DERIVED** |
| **Model Loading** | YES | Loaded once in constructor, wrapped in `try/except` | **LEGACY-DERIVED** |
| **Animal Classes** | YES | 29 verified classes in `modules/animal_detection.py` lines 18-23 | **LEGACY-DERIVED** |
| **Confidence Threshold** | YES | `conf > 0.5` in `modules/animal_detection.py:53`; `ProjectSettings.detection_confidence_threshold` default 0.50 | **LEGACY-DERIVED** |
| **Threat Levels** | YES | `config.json` lines 4-50 and `ProjectSettings.threat_level_overrides` ('high', 'medium', 'low') | **LEGACY-DERIVED** |
| **Camera Index & Init** | YES | `cv2.VideoCapture(0)` in `modules/animal_detection.py:98`; `ProjectSettings.camera_device_index` default 0 | **LEGACY-DERIVED** |
| **Live Streaming** | YES | MJPEG multipart `multipart/x-mixed-replace; boundary=frame` in `app.py:70` | **LEGACY-DERIVED** |
| **AnimalLog Creation** | YES | `INSERT INTO animal_logs (animal_type, confidence, timestamp, field, image_path)` in `modules/animal_detection.py:85-87` | **LEGACY-DERIVED** |
| **Alert Triggering** | YES | `INSERT INTO alerts (animal_log_id, alert_type, status)` in `modules/alerts.py:14-15` ('Email + Buzzer', 'Email', 'Log Only') | **LEGACY-DERIVED** |
| **Cooldown Suppression** | YES | `current_time - last_notification_time >= notification_cooldown` in `modules/animal_detection.py:74`; `ProjectSettings.alert_cooldown_seconds` | **LEGACY-DERIVED** |
| **Image Analysis API** | NO | Dedicated manual image upload API (`POST /api/v1/detection/analyze/`) | **NEW DJANGO/API ENHANCEMENT** |
| **Detection Status API** | NO | Engine health and settings retrieval (`GET /api/v1/detection/status/`) | **NEW DJANGO/API ENHANCEMENT** |
| **Detection Toggle** | YES | Legacy `/toggle_detection` route (`app.py:73-76`) migrated to `PATCH /api/v1/detection/status/` | **LEGACY-DERIVED & ENHANCED** |

---

## 3. Endpoints Reference

Base path: `/api/v1/detection/`

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/detection/status/` | Authenticated | Retrieves YOLO engine health, active settings, and supported species. |
| `PATCH` | `/api/v1/detection/status/` | Staff / Admin | Toggles the detection engine master switch (`detection_enabled`). |
| `POST` | `/api/v1/detection/analyze/` | Authenticated | Uploads an image file for immediate YOLO inference, threat scoring, and logging. |
| `GET` | `/api/v1/detection/stream/` | Authenticated | Live MJPEG multipart video feed. |
| `GET` | `/api/v1/detection/logs/` | Authenticated | Lists historical `AnimalLog` records with query filters. |
| `GET` | `/api/v1/detection/logs/{id}/` | Authenticated | Retrieves detailed data for a specific detection event. |

---

## 4. Request & Response Examples

### 4.1 Get Detection Status (`GET /api/v1/detection/status/`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Detection status retrieved successfully.",
    "data": {
      "detection_enabled": true,
      "engine_available": true,
      "model_name": "YOLOv8n",
      "confidence_threshold": 0.5,
      "camera_device_index": 0,
      "alert_cooldown_seconds": 60,
      "audio_buzzer_enabled": true,
      "email_alerts_enabled": true,
      "supported_classes_count": 29,
      "supported_classes": [
        "cat", "dog", "horse", "sheep", "cow", "elephant", "bear",
        "zebra", "giraffe", "lion", "tiger", "cheetah", "monkey",
        "leopard", "wolf", "fox", "deer", "hippo", "hyena",
        "jackal", "kangaroo", "squirrel", "penguin", "eagle",
        "owl", "snake", "crocodile", "mouse", "rat"
      ]
    }
  }
  ```

---

### 4.2 Toggle Detection (`PATCH /api/v1/detection/status/`)
- **Request**:
  ```json
  {
    "detection_enabled": false
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Detection status updated successfully.",
    "data": {
      "detection_enabled": false,
      "engine_available": true,
      "model_name": "YOLOv8n",
      "confidence_threshold": 0.5,
      "camera_device_index": 0,
      "alert_cooldown_seconds": 60,
      "audio_buzzer_enabled": true,
      "email_alerts_enabled": true,
      "supported_classes_count": 29,
      "supported_classes": [...]
    }
  }
  ```

---

### 4.3 Analyze Uploaded Image (`POST /api/v1/detection/analyze/`)
- **Request**: `multipart/form-data` with `image` file and optional `field` string.
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Image analysis completed successfully.",
    "data": {
      "detection_enabled": true,
      "detections_count": 1,
      "detections": [
        {
          "label": "wolf",
          "confidence": 0.9452,
          "threat_level": "high",
          "box": [120, 85, 340, 410]
        }
      ],
      "highest_threat_animal": "wolf",
      "highest_threat_level": "high",
      "highest_confidence": 0.9452,
      "animal_log": {
        "id": 14,
        "animal_type": "wolf",
        "confidence": 0.9452,
        "timestamp": "2026-08-24T15:45:00.000Z",
        "field": "North Perimeter",
        "image_path": "detections/detected_wolf_1777285500.jpg"
      },
      "alert_triggered": true,
      "alert_type": "Email + Buzzer"
    }
  }
  ```

---

### 4.4 List Animal Logs (`GET /api/v1/detection/logs/?animal_type=wolf&min_confidence=0.80`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Animal detection logs retrieved successfully.",
    "data": [
      {
        "id": 14,
        "animal_type": "wolf",
        "confidence": 0.9452,
        "timestamp": "2026-08-24T15:45:00Z",
        "field": "North Perimeter",
        "image_path": "detections/detected_wolf_1777285500.jpg",
        "created_at": "2026-08-24T15:45:00Z",
        "updated_at": "2026-08-24T15:45:00Z"
      }
    ]
  }
  ```
