# FarmSync Dashboard & Analytics API Specification (Step 6)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 6 – Read-Only Dashboard API Layer  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED (With Complete Legacy Evidence)  

---

## 1. Step Objective & Architectural Boundary

The **Dashboard Module** (`apps.dashboard`) provides an authenticated, read-only analytics and activity aggregation layer. It calculates metrics on-demand directly from authoritative domain models (`Farmer`, `Attendance`, `Task`, `AnimalLog`, `Alert`).

### Core Architecture Rules:
1. **Zero Duplicate Persistent Models**: The dashboard maintains zero persistent models or database tables. All metrics are computed dynamically at query time from authoritative domain tables.
2. **Dedicated Service Layer**: All analytical query aggregations and timezone calculations reside in `DashboardService` (`apps/dashboard/services.py`), keeping views lightweight and decoupled.
3. **Decoupled Frontend Consumption**: Returns standard JSON API response envelopes compatible with the legacy web interface, modern React/Vue SPAs, mobile applications, and Lovable AI-generated client interfaces.

---

## 2. Legacy Evidence Matrix

Every status string and metric in the Dashboard API has been verified against the original legacy codebase (`app.py`, `modules/*.py`, `templates/*.html`) and the legacy SQLite database (`data.db`):

| Value / Metric | Table / Domain | Exact Legacy Evidence Source | Legacy Verified | Classification |
| :--- | :--- | :--- | :--- | :--- |
| `farmers.total_farmers` | `Farmer` | `app.py` line 32 (`SELECT COUNT(*) as c FROM farmers`), `templates/dashboard.html` line 37 (`{{ total_farmers }}`) | **YES** | **LEGACY-DERIVED** |
| `attendance.today_attendance` | `Attendance` | `app.py` line 35 (`SELECT COUNT(*) as c FROM attendance WHERE date = ?`), `templates/dashboard.html` line 41 (`{{ today_attendance }}`) | **YES** | **LEGACY-DERIVED** |
| `attendance.total_records` | `Attendance` | Not on legacy dashboard (calculated via `Attendance.objects.count()`) | **N/A** | **NEW DJANGO ENHANCEMENT** |
| `alerts.alerts_today` | `Alert` + `AnimalLog` | `app.py` line 37 (`SELECT COUNT(*) as c FROM alerts a JOIN animal_logs al ON a.animal_log_id = al.id WHERE al.timestamp LIKE ?`), `templates/dashboard.html` line 45 (`{{ alerts_today }}`) | **YES** | **LEGACY-DERIVED** |
| `alerts.total_alerts` | `Alert` | Not on legacy dashboard (calculated via `Alert.objects.count()`) | **N/A** | **NEW DJANGO ENHANCEMENT** |
| `alerts.triggered_alerts` | `Alert` (`status='Triggered'`) | `modules/alerts.py` line 14 (`INSERT INTO alerts (animal_log_id, alert_type, status) VALUES (?, ?, 'Triggered')`), `data.db` (rows 1 & 2 in `alerts` have `status='Triggered'`) | **YES** | **NEW DJANGO ENHANCEMENT** |
| `tasks.completed_tasks` | `Task` (`status='Completed'`) | `app.py` line 39 (`SELECT COUNT(*) as c FROM tasks WHERE status = 'Completed'`), `templates/dashboard.html` line 49 (`{{ completed_tasks }}`), `templates/tasks.html` line 65 (`value="Completed"`), `data.db` (`tasks` row 1 has `status='Completed'`) | **YES** | **LEGACY-DERIVED** |
| `tasks.pending_tasks` | `Task` (`status='Pending'`) | `modules/tasks.py` line 6 (`INSERT INTO tasks (task_name, assigned_to, status, date) VALUES (?, ?, 'Pending', ?)`), `templates/tasks.html` line 62 (`{% if task.status == 'Pending' %}`) | **YES** | **NEW DJANGO ENHANCEMENT** |
| `tasks.total_tasks` | `Task` | Not on legacy dashboard (calculated via `Task.objects.count()`) | **N/A** | **NEW DJANGO ENHANCEMENT** |
| `detections.detections_today` | `AnimalLog` | Not on legacy dashboard (calculated via `AnimalLog.objects.filter(timestamp__gte=today_start).count()`) | **N/A** | **NEW DJANGO ENHANCEMENT** |
| `detections.total_detections` | `AnimalLog` | Not on legacy dashboard (calculated via `AnimalLog.objects.count()`) | **N/A** | **NEW DJANGO ENHANCEMENT** |
| `recent_activity.recent_alerts` | `Alert` | Originally on `templates/alerts.html` via `modules/alerts.py` line 81 (`get_recent_alerts()`); unified into dashboard API | **YES (as alert view)** | **NEW DJANGO ENHANCEMENT** |
| `recent_activity.recent_detections` | `AnimalLog` | Originally on `templates/alerts.html` via `app.py` line 157 (`SELECT * FROM animal_logs... LIMIT 50`); unified into dashboard API | **YES (as alert view)** | **NEW DJANGO ENHANCEMENT** |
| `recent_activity.recent_tasks` | `Task` | Originally on `templates/tasks.html` via `modules/tasks.py` line 13 (`get_all_tasks()`); unified into dashboard API | **YES (as task view)** | **NEW DJANGO ENHANCEMENT** |

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
