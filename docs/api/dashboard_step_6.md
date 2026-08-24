# FarmSync Dashboard & Analytics API Specification (Step 6)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 6 – Read-Only Dashboard API Layer  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Step Objective & Architecture Overview

The **Dashboard Module** (`apps.dashboard`) provides an authenticated, read-only analytics and aggregation layer. It aggregates data on-demand directly from authoritative domain models (`Farmer`, `Attendance`, `Task`, `AnimalLog`, `Alert`).

### Core Architectural Decisions:
1. **Zero Duplicate Persistent Models**: The dashboard maintains zero persistent models or database tables. All metrics are computed dynamically at query time from authoritative domain tables.
2. **Dedicated Service Layer**: All analytical query aggregations and timezone calculations reside in `DashboardService` (`apps/dashboard/services.py`), keeping views lightweight and decoupled.
3. **Decoupled Frontend Consumption**: Returns standard JSON API response envelopes compatible with the legacy web interface, modern React/Vue SPAs, mobile applications, and Lovable AI-generated client interfaces.

---

## 2. Field Classification & Source Mapping

| Response Field | Source Domain Model | Classification | Description |
| :--- | :--- | :--- | :--- |
| `farmers.total_farmers` | `apps.farmers.models.Farmer` | **LEGACY-DERIVED** | Total count of registered farm workers (`SELECT COUNT(*) FROM farmers`). |
| `attendance.today_attendance` | `apps.attendance.models.Attendance` | **LEGACY-DERIVED** | Number of worker check-ins for the current calendar date (`date = today`). |
| `attendance.total_records` | `apps.attendance.models.Attendance` | **NEW DJANGO ENHANCEMENT** | Total lifetime attendance check-in/out records. |
| `alerts.alerts_today` | `apps.alerts.models.Alert` | **LEGACY-DERIVED** | Count of alerts triggered today (`timestamp >= today_start`). |
| `alerts.total_alerts` | `apps.alerts.models.Alert` | **NEW DJANGO ENHANCEMENT** | Total lifetime alert notifications. |
| `alerts.triggered_alerts` | `apps.alerts.models.Alert` | **NEW DJANGO ENHANCEMENT** | Count of alerts with active status `'Triggered'`. |
| `tasks.completed_tasks` | `apps.tasks.models.Task` | **LEGACY-DERIVED** | Count of tasks with status `'Completed'`. |
| `tasks.pending_tasks` | `apps.tasks.models.Task` | **NEW DJANGO ENHANCEMENT** | Count of tasks with status `'Pending'`. |
| `tasks.total_tasks` | `apps.tasks.models.Task` | **NEW DJANGO ENHANCEMENT** | Total count of all tasks. |
| `detections.detections_today` | `apps.detection.models.AnimalLog` | **NEW DJANGO ENHANCEMENT** | Number of vision detection logs recorded today. |
| `detections.total_detections` | `apps.detection.models.AnimalLog` | **NEW DJANGO ENHANCEMENT** | Total lifetime vision detection logs recorded. |
| `recent_activity.recent_alerts` | `apps.alerts.models.Alert` | **LEGACY-DERIVED** | Latest N alert notifications with animal species and timestamps. |
| `recent_activity.recent_detections` | `apps.detection.models.AnimalLog` | **NEW DJANGO ENHANCEMENT** | Latest N camera vision logs with confidence and image paths. |
| `recent_activity.recent_tasks` | `apps.tasks.models.Task` | **NEW DJANGO ENHANCEMENT** | Latest N task assignments with worker names and status. |

---

## 3. Endpoints Reference

### 3.1 Primary Summary Endpoint
- **URL**: `GET /api/v1/dashboard/summary/`
- **Permissions**: `IsAuthenticated` (Requires `Authorization: Bearer <access_token>`)
- **HTTP Methods**: `GET` only (`POST`, `PUT`, `DELETE` are rejected with `405 Method Not Allowed`)

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully.",
  "data": {
    "date": "2026-08-24",
    "farmers": {
      "total_farmers": 12
    },
    "attendance": {
      "today_attendance": 9,
      "total_records": 140
    },
    "tasks": {
      "total_tasks": 20,
      "completed_tasks": 14,
      "pending_tasks": 6
    },
    "detections": {
      "detections_today": 4,
      "total_detections": 85
    },
    "alerts": {
      "alerts_today": 2,
      "total_alerts": 38,
      "triggered_alerts": 2
    }
  }
}
```

---

### 3.2 Recent Activity Endpoint
- **URL**: `GET /api/v1/dashboard/recent-activity/`
- **Permissions**: `IsAuthenticated`
- **Query Parameters**: `limit` (Optional integer, default: 5, maximum: 20)

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Dashboard recent activity retrieved successfully.",
  "data": {
    "recent_alerts": [
      {
        "id": 1,
        "animal_type": "wolf",
        "alert_type": "Email + Buzzer",
        "status": "Triggered",
        "timestamp": "2026-08-24T12:30:00Z"
      }
    ],
    "recent_detections": [
      {
        "id": 1,
        "animal_type": "wolf",
        "confidence": 0.88,
        "field": "North Field",
        "image_path": "detections/detected_wolf_1724509920.jpg",
        "timestamp": "2026-08-24T12:30:00Z"
      }
    ],
    "recent_tasks": [
      {
        "id": 1,
        "task_name": "Check drip irrigation line",
        "assigned_to_name": "Farmer John",
        "status": "Pending",
        "date": "2026-08-24"
      }
    ]
  }
}
```

---

## 4. Timezone & Zero-Data Guarantees

1. **Deterministic Timezone Calculation**:
   - Computes calendar dates using `django.utils.timezone.localdate()` configured to the server's timezone (`settings.TIME_ZONE = 'Asia/Kolkata'`).
   - Computes day boundaries using `timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)` to avoid naive datetime comparison errors.
2. **Zero-Data State Handling**:
   - If the database is empty, the API returns `200 OK` with zero counts (`0`) and empty activity arrays (`[]`). It will never crash or raise unhandled exceptions.

---

## 5. Security & Read-Only Policy

- **Authentication Required**: Protected by SimpleJWT `IsAuthenticated`.
- **Strictly Read-Only**: Endpoints only respond to HTTP `GET`. Any mutating request (`POST`, `PUT`, `DELETE`) is rejected with `405 Method Not Allowed`.
- **Zero Sensitive Data Exposure**: Response payloads never contain passwords, tokens, API keys, or SMTP credentials.
