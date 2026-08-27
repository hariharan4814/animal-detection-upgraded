# FarmSync Final REST API Directory & Endpoint Index

**Project**: FarmSync / Intelligent Animal Detection System  
**Document**: Complete API Specification & Endpoint Index  
**Base URL**: `/api/v1/`  
**Standard Response Envelope**: `{"success": true|false, "message": "...", "data": {...}, "errors": null}`  

---

## 1. Authentication Endpoints (`/api/v1/auth/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login/` | No (`AllowAny`) | Public | Validates user credentials; returns JWT `access` token, `refresh` token, and user profile. |
| `POST` | `/api/v1/auth/refresh/` | No (`AllowAny`) | Public | Submits valid `refresh` token; returns newly rotated `access` and `refresh` tokens. |
| `GET` | `/api/v1/auth/me/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves profile details and permissions for the currently authenticated user. |
| `POST` | `/api/v1/auth/logout/` | Yes (`IsAuthenticated`) | Any Worker | Submits `refresh` token to blacklist; invalidates token for subsequent use. |

---

## 2. Dashboard Analytics (`/api/v1/dashboard/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary/` | Yes (`IsAuthenticated`) | Any Worker | Returns real-time aggregate KPI counts (`total_farmers`, `farmers_present_today`, `pending_tasks`, `total_alerts`). |
| `GET` | `/api/v1/dashboard/recent-activity/` | Yes (`IsAuthenticated`) | Any Worker | Returns chronological activity feed combining recent animal detections, alerts, and shift logs. |

---

## 3. Farmers Roster Management (`/api/v1/farmers/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/farmers/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves paginated or complete workforce list with contact info and assigned sectors. |
| `POST` | `/api/v1/farmers/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Registers a new farmer (`name`, `phone`, `field`, `email`). |
| `GET` | `/api/v1/farmers/<id>/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves full profile and details for a specific farmer. |
| `PUT` | `/api/v1/farmers/<id>/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Full update of farmer record. |
| `PATCH`| `/api/v1/farmers/<id>/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Partial update of farmer record. |
| `DELETE`| `/api/v1/farmers/<id>/`| Yes (`IsAdminOrReadOnly`) | Staff / Admin | Deletes farmer record; cascades attendance records and nullifies task assignments. |

---

## 4. Attendance & Shift Tracking (`/api/v1/attendance/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/attendance/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves attendance logs. Supports query filters (`?date=`, `?farmer_id=`). |
| `POST` | `/api/v1/attendance/check-in/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Records shift arrival time and optional GPS location. Duplicate check-in on same day returns 400. |
| `POST` | `/api/v1/attendance/check-out/`| Yes (`IsAdminOrReadOnly`) | Staff / Admin | Records shift departure time; automatically computes total shift hours (`total_hours`). |
| `GET` | `/api/v1/attendance/report/` | Yes (`IsAuthenticated`) | Any Worker | Generates multi-day aggregate attendance and hours summary per worker. |

---

## 5. Tasks Management (`/api/v1/tasks/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/tasks/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves task list. Supports filtering by status (`?status=Pending` or `?status=Completed`). |
| `POST` | `/api/v1/tasks/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Creates a new agricultural task assigned to a farmer. |
| `GET` | `/api/v1/tasks/<id>/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves task details. |
| `PUT` | `/api/v1/tasks/<id>/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Full update of task details. |
| `PATCH`| `/api/v1/tasks/<id>/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Partial update (e.g. toggling `status` between `Pending` and `Completed`). |
| `DELETE`| `/api/v1/tasks/<id>/`| Yes (`IsAdminOrReadOnly`) | Staff / Admin | Deletes task record. |

---

## 6. Computer Vision, Detection & Live Camera (`/api/v1/detection/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/detection/status/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves YOLO engine status, active confidence threshold, camera index, and supported species. |
| `POST` | `/api/v1/detection/status/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Updates master detection toggle (`{"detection_enabled": true|false}`). |
| `POST` | `/api/v1/detection/analyze/`| Yes (`IsAuthenticated`) | Any Worker | Uploads an image (`multipart/form-data`) for YOLO inference; logs detections and dispatches alerts. |
| `GET` | `/api/v1/detection/stream/` | Yes (`IsAuthenticated`) | Any Worker | Live multipart MJPEG video stream (`multipart/x-mixed-replace`). Supports Bearer header & `?token=<jwt>`. |
| `GET` | `/api/v1/detection/logs/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves historical animal detection logs and snapshot file paths. |
| `GET` | `/api/v1/detection/logs/<id>/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves specific animal detection log event. |

---

## 7. Hazard Alerts (**Strictly Immutable**) (`/api/v1/alerts/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/alerts/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves immutable hazard alert history. Supports filters (`?status=`, `?alert_type=`). |
| `GET` | `/api/v1/alerts/<id>/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves specific alert event and linked `AnimalLog` reference. |
| `GET` | `/api/v1/alerts/summary/` | Yes (`IsAuthenticated`) | Any Worker | Returns summary statistics on triggered alerts by dispatch channel. |
| `POST/PUT/DELETE` | `/api/v1/alerts/*` | N/A | Forbidden | **Rejected with HTTP 405 Method Not Allowed** to maintain an untampered historical audit trail. |

---

## 8. System & Notification Settings (`/api/v1/settings/`)

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/settings/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves global `ProjectSettings` singleton (thresholds, cooldowns, camera index, wage). |
| `PUT/PATCH` | `/api/v1/settings/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Updates runtime project settings without requiring server restart. |
| `GET` | `/api/v1/settings/email-sender/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves SMTP dispatcher config (`smtp_password_configured` returned, password masked). |
| `PUT/PATCH` | `/api/v1/settings/email-sender/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Updates SMTP credentials (passwords processed write-only). |
| `GET` | `/api/v1/settings/receivers/` | Yes (`IsAuthenticated`) | Any Worker | Retrieves active email alert recipient list. |
| `POST` | `/api/v1/settings/receivers/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Adds a new alert email recipient. |
| `DELETE`| `/api/v1/settings/receivers/<id>/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Removes an email recipient. |
| `POST` | `/api/v1/settings/receivers/bulk/` | Yes (`IsAdminOrReadOnly`) | Staff / Admin | Replaces the entire alert recipient roster in a single atomic transaction. |
