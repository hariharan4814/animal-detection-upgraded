# FarmSync REST API Contract & Specification

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 0 – Audit & Architecture Assessment  
**Date**: August 2026  
**Status**: SPECIFICATION ONLY (Blueprint for Future DRF Implementation)  
**Standard**: OpenAPI 3.0 Compatible REST / JSON Specification  

---

## 1. API-First Architecture Principles

To enable total decoupling of the frontend (allowing the user interface to be developed, refactored, or replaced using Lovable AI or any SPA framework without modifying backend logic), the FarmSync Django backend adheres strictly to the following API-First principles:

1. **Stateless REST Communication**: Every request carries its own authentication credentials via HTTP `Authorization: Bearer <token>` headers.
2. **Standardized JSON Envelopes**: All resource endpoints accept and return JSON payloads formatted in camelCase or snake_case conventions with standard HTTP status codes.
3. **Complete Backend Authority**:
   - The backend enforces all validation, business logic, authorization rules, and data integrity checks.
   - The frontend is strictly a presentation and interaction layer.
4. **Secret Masking Guarantee**: Sensitive credentials (such as SMTP passwords or secret keys) are write-only and are **never** returned across the API wire.
5. **Deterministic Error Formats**: Errors are returned in a predictable schema indicating error code, human-readable message, and field-level validation details.

---

## 2. Authentication & Authorization Strategy

### 2.1 Authentication Mechanism
- **Protocol**: JSON Web Token (JWT) using `djangorestframework-simplejwt`.
- **Token Lifetime**: 
  - Access Token: 60 minutes
  - Refresh Token: 7 days (with automatic token rotation)
- **Header Format**: `Authorization: Bearer <access_token>`

### 2.2 Role-Based Access Control (RBAC)
| Role | Identifier | Permitted Operations |
| :--- | :--- | :--- |
| **Administrator / Farm Manager** | `admin` | Full read/write access to all endpoints (Settings, Hardware Controls, Workforce, Attendance, Tasks, Detection, Alerts, Accounts). |
| **Field Worker / Operator** | `worker` | Read-only access to camera feeds and alert logs; permission to trigger personal check-in/out and update personal assigned tasks. |
| **Auditor / Viewer** | `viewer` | Read-only access to dashboard statistics, attendance logs, and detection histories. |

---

## 3. Proposed API Resources & Endpoint Map

### 3.1 Module: Authentication (`/api/auth/`)

#### `POST /api/auth/login/`
- **Purpose**: Authenticate user credentials and issue JWT pair.
- **Authorized Roles**: Public / Unauthenticated
- **Current Flask Source**: None (New Feature)
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "SecurePassword123"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@farmsync.local",
      "role": "admin",
      "first_name": "Farm",
      "last_name": "Administrator"
    }
  }
  ```

#### `POST /api/auth/refresh/`
- **Purpose**: Refresh an expired access token using a valid refresh token.
- **Authorized Roles**: Public
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

#### `GET /api/auth/me/`
- **Purpose**: Retrieve current logged-in user profile.
- **Authorized Roles**: Authenticated (`admin`, `worker`, `viewer`)
- **Response Payload (`200 OK`)**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@farmsync.local",
    "role": "admin",
    "is_active": true
  }
  ```

---

### 3.2 Module: Dashboard (`/api/dashboard/`)

#### `GET /api/dashboard/stats/`
- **Purpose**: Fetch top-level aggregate statistics for the dashboard cards.
- **Authorized Roles**: Authenticated (`admin`, `worker`, `viewer`)
- **Current Flask Source**: `app.py:dashboard()` (Lines 29-45)
- **Response Payload (`200 OK`)**:
  ```json
  {
    "total_farmers": 12,
    "today_attendance": 9,
    "alerts_today": 3,
    "completed_tasks": 18,
    "pending_tasks": 4,
    "system_status": {
      "camera_active": true,
      "detection_active": true,
      "last_detection_timestamp": "2026-08-24T14:32:00Z"
    }
  }
  ```

---

### 3.3 Module: Farmers Workforce (`/api/farmers/`)

#### `GET /api/farmers/`
- **Purpose**: Retrieve list of all registered farmers with optional search and filtering.
- **Authorized Roles**: Authenticated (`admin`, `worker`, `viewer`)
- **Current Flask Source**: `app.py:manage_farmers()` (Lines 140-143)
- **Query Parameters**: `?search=john&field=North+Field`
- **Response Payload (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "name": "John Doe",
      "phone": "+1234567890",
      "email": "john@example.com",
      "field": "North Field",
      "created_at": "2026-08-24T10:00:00Z"
    }
  ]
  ```

#### `POST /api/farmers/`
- **Purpose**: Register a new farmer.
- **Authorized Roles**: `admin`
- **Current Flask Source**: `app.py:add_farmer()` (Lines 145-154)
- **Request Body**:
  ```json
  {
    "name": "Michael Green",
    "phone": "+1987654321",
    "email": "michael@example.com",
    "field": "East Orchard"
  }
  ```
- **Response Payload (`201 Created`)**: Returns created farmer object.

#### `GET /api/farmers/{id}/`
- **Purpose**: Retrieve a single farmer's details including attendance history summary.
- **Authorized Roles**: Authenticated

#### `PUT / PATCH /api/farmers/{id}/`
- **Purpose**: Update farmer information.
- **Authorized Roles**: `admin`

#### `DELETE /api/farmers/{id}/`
- **Purpose**: Remove a farmer from the system.
- **Authorized Roles**: `admin`
- **Current Flask Source**: `app.py:delete_farmer()` (Lines 156-159)
- **Response Payload (`204 No Content`)**

---

### 3.4 Module: Attendance & Geolocation (`/api/attendance/`)

#### `POST /api/attendance/check-in/`
- **Purpose**: Record farmer check-in with GPS location and dispatch email confirmation.
- **Authorized Roles**: `admin`, `worker`
- **Current Flask Source**: `app.py:check_in()` (Lines 84-90) & `modules/attendance.py:mark_check_in()`
- **Request Body**:
  ```json
  {
    "farmer_id": 1,
    "device_location": "12.9716, 77.5946"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Check-in recorded successfully.",
    "attendance": {
      "id": 14,
      "farmer_id": 1,
      "farmer_name": "John Doe",
      "date": "2026-08-24",
      "check_in": "08:15:30",
      "check_out": null,
      "total_hours": 0.0,
      "location": "12.9716, 77.5946"
    }
  }
  ```

#### `POST /api/attendance/check-out/`
- **Purpose**: Record farmer check-out, compute elapsed hours, and dispatch confirmation email.
- **Authorized Roles**: `admin`, `worker`
- **Current Flask Source**: `app.py:check_out()` (Lines 92-98) & `modules/attendance.py:mark_check_out()`
- **Request Body**:
  ```json
  {
    "farmer_id": 1,
    "device_location": "12.9716, 77.5946"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Check-out recorded successfully.",
    "attendance": {
      "id": 14,
      "farmer_id": 1,
      "farmer_name": "John Doe",
      "date": "2026-08-24",
      "check_in": "08:15:30",
      "check_out": "17:30:10",
      "total_hours": 9.24,
      "location": "12.9716, 77.5946"
    }
  }
  ```

#### `GET /api/attendance/logs/`
- **Purpose**: List today's or recent attendance logs.
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `app.py:attendance_page()` (Lines 51-55)

#### `GET /api/attendance/reports/`
- **Purpose**: Query attendance logs filtered by date range and farmer ID.
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `app.py:attendance_report()` (Lines 117-137)
- **Query Parameters**: `?start_date=2026-08-01&end_date=2026-08-24&farmer_id=1`
- **Response Payload (`200 OK`)**:
  ```json
  {
    "total_records": 1,
    "start_date": "2026-08-01",
    "end_date": "2026-08-24",
    "results": [
      {
        "id": 14,
        "farmer_name": "John Doe",
        "date": "2026-08-24",
        "check_in": "08:15:30",
        "check_out": "17:30:10",
        "total_hours": 9.24,
        "location": "12.9716, 77.5946",
        "map_url": "https://maps.google.com/?q=12.9716,77.5946"
      }
    ]
  }
  ```

---

### 3.5 Module: Task Management (`/api/tasks/`)

#### `GET /api/tasks/`
- **Purpose**: List all tasks with status and assignee details.
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `app.py:tasks_page()` (Lines 57-61) & `modules/tasks.py:get_all_tasks()`
- **Query Parameters**: `?status=Pending&assigned_to=1`
- **Response Payload (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "task_name": "Inspect irrigation lines",
      "assigned_to": 1,
      "assigned_to_name": "John Doe",
      "status": "Pending",
      "date": "2026-08-24"
    }
  ]
  ```

#### `POST /api/tasks/`
- **Purpose**: Create a new task assignment.
- **Authorized Roles**: `admin`
- **Current Flask Source**: `app.py:add_new_task()` (Lines 101-107) & `modules/tasks.py:add_task()`
- **Request Body**:
  ```json
  {
    "task_name": "Harvest South Vineyard",
    "assigned_to": 1
  }
  ```
- **Response Payload (`201 Created`)**

#### `PATCH /api/tasks/{id}/status/`
- **Purpose**: Update the status of an existing task (e.g., mark 'Completed').
- **Authorized Roles**: `admin`, `worker`
- **Current Flask Source**: `app.py:update_task()` (Lines 109-115) & `modules/tasks.py:update_task_status()`
- **Request Body**:
  ```json
  {
    "status": "Completed"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "id": 1,
    "status": "Completed",
    "updated_at": "2026-08-24T16:00:00Z"
  }
  ```

---

### 3.6 Module: Detection & Camera Hardware (`/api/detection/`)

#### `GET /api/detection/camera/stream/`
- **Purpose**: Dedicated MJPEG live video stream endpoint with overlay bounding boxes.
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `app.py:video_feed()` (Lines 68-71)
- **Response Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Behavior**: Returns continuous boundary-delimited JPEG frames.

#### `GET /api/detection/camera/status/`
- **Purpose**: Retrieve current camera hardware state, inference state, and framerate.
- **Authorized Roles**: Authenticated
- **Response Payload (`200 OK`)**:
  ```json
  {
    "camera_on": true,
    "detect_enabled": true,
    "device_index": 0,
    "fps": 24.0,
    "active_stream_subscribers": 1
  }
  ```

#### `POST /api/detection/camera/toggle/`
- **Purpose**: Turn camera hardware feed active or blank.
- **Authorized Roles**: `admin`
- **Current Flask Source**: `app.py:toggle_camera()` (Lines 78-81)
- **Response Payload (`200 OK`)**:
  ```json
  {
    "status": "success",
    "camera_on": false
  }
  ```

#### `POST /api/detection/camera/detection/toggle/`
- **Purpose**: Turn YOLO detection inference on or off during live streaming.
- **Authorized Roles**: `admin`
- **Current Flask Source**: `app.py:toggle_detection()` (Lines 73-76)
- **Response Payload (`200 OK`)**:
  ```json
  {
    "status": "success",
    "detect": true
  }
  ```

#### `GET /api/detection/logs/`
- **Purpose**: Paginated list of detected animal events and snapshot image URLs.
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `app.py:alerts_page()` (Lines 63-66)
- **Query Parameters**: `?page=1&threat_level=high&animal_type=lion`
- **Response Payload (`200 OK`)**:
  ```json
  {
    "count": 42,
    "next": "/api/detection/logs/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "animal_type": "wolf",
        "confidence": 0.892,
        "confidence_percentage": "89.2%",
        "threat_level": "high",
        "field": "Main Field",
        "timestamp": "2026-08-24T14:32:00Z",
        "image_url": "http://localhost:8000/media/detections/detected_wolf_1724509920.jpg"
      }
    ]
  }
  ```

---

### 3.7 Module: Alerts & Notifications (`/api/alerts/`)

#### `GET /api/alerts/`
- **Purpose**: Query history of triggered alerts (Email, Buzzer, Log Only).
- **Authorized Roles**: Authenticated
- **Current Flask Source**: `modules/alerts.py:get_recent_alerts()`
- **Response Payload (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "animal_log_id": 1,
      "animal_type": "wolf",
      "alert_type": "Email + Buzzer",
      "threat_level": "high",
      "status": "Triggered",
      "timestamp": "2026-08-24T14:32:00Z"
    }
  ]
  ```

#### `POST /api/alerts/test/`
- **Purpose**: Trigger a test alert notification (email/buzzer) to verify SMTP settings.
- **Authorized Roles**: `admin`
- **Request Body**:
  ```json
  {
    "type": "email",
    "target_email": "admin@example.com"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "Test notification dispatched."
  }
  ```

---

### 3.8 Module: Settings (`/api/settings/`)

#### `GET /api/settings/general/`
- **Purpose**: Get general farm and wage parameters.
- **Authorized Roles**: Authenticated
- **Response Payload (`200 OK`)**:
  ```json
  {
    "project_name": "FarmSync Smart Farm",
    "farm_location": "Main Field",
    "timezone": "Asia/Kolkata",
    "work_start_time": "08:00",
    "wage_per_hour": 15.00
  }
  ```

#### `PUT / PATCH /api/settings/general/`
- **Purpose**: Update general farm parameters.
- **Authorized Roles**: `admin`

#### `GET /api/settings/email-sender/`
- **Purpose**: Get current SMTP sender configuration (**with password masked**).
- **Authorized Roles**: `admin`
- **Response Payload (`200 OK`)**:
  ```json
  {
    "sender_email": "alerts@farmsync.local",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "has_password": true
  }
  ```

#### `PUT / PATCH /api/settings/email-sender/`
- **Purpose**: Update SMTP sender configuration (**write-only password**).
- **Authorized Roles**: `admin`
- **Request Body**:
  ```json
  {
    "sender_email": "alerts@farmsync.local",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "sender_password": "NewAppPassword123"
  }
  ```

#### `GET /api/settings/email-receivers/`
- **Purpose**: List of alert recipient email addresses.
- **Authorized Roles**: `admin`
- **Response Payload (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "email": "manager@farm.com",
      "receive_high_threat": true,
      "receive_medium_threat": true,
      "is_active": true
    }
  ]
  ```

#### `POST /api/settings/email-receivers/`
- **Purpose**: Add an alert recipient email.
- **Authorized Roles**: `admin`

#### `DELETE /api/settings/email-receivers/{id}/`
- **Purpose**: Remove an alert recipient.
- **Authorized Roles**: `admin`

#### `GET /api/settings/threat-rules/`
- **Purpose**: Get current animal threat classification map (e.g., lion -> high, deer -> low).
- **Authorized Roles**: Authenticated
- **Response Payload (`200 OK`)**:
  ```json
  {
    "confidence_threshold": 0.50,
    "notification_cooldown_seconds": 300,
    "threat_levels": {
      "lion": "high",
      "tiger": "high",
      "bear": "high",
      "elephant": "medium",
      "deer": "low"
    }
  }
  ```

#### `PATCH /api/settings/threat-rules/`
- **Purpose**: Modify confidence threshold, cooldown, or species threat level.
- **Authorized Roles**: `admin`
- **Request Body**:
  ```json
  {
    "confidence_threshold": 0.60,
    "notification_cooldown_seconds": 180,
    "threat_levels": {
      "monkey": "medium"
    }
  }
  ```

---

## 4. Error Response & Status Code Guidelines

All API responses follow consistent HTTP status code semantics and unified error structures:

### Standard Error Response Envelope
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided input data failed validation.",
    "details": {
      "phone": ["This field must contain a valid phone number."],
      "field": ["This field is required."]
    }
  }
}
```

### Standard HTTP Status Codes
- `200 OK`: Request succeeded, returns requested data.
- `201 Created`: Resource created successfully.
- `204 No Content`: Resource deleted successfully.
- `400 Bad Request`: Request payload malformed or validation failed.
- `401 Unauthorized`: Missing, expired, or invalid JWT token.
- `403 Forbidden`: Authenticated user lacks role permissions.
- `404 Not Found`: Requested resource does not exist.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Unhandled server exception.

---

## 5. Streaming Endpoint Strategy (MJPEG vs Alternatives)

1. **Primary Feed (`/api/detection/camera/stream/`)**:
   - Implemented via Django `StreamingHttpResponse(generator, content_type='multipart/x-mixed-replace; boundary=frame')`.
   - Native browser integration: The decoupled frontend displays the stream simply by pointing an HTML image element `<img src="http://localhost:8000/api/detection/camera/stream/" />` with authenticated query token or CORS session.
2. **Lifecycle Control**:
   - The video capture hardware is managed by a background service thread in `services/camera/`.
   - When no clients are subscribed to `/stream/`, the capture thread pauses frame encoding to minimize CPU consumption.
   - Frontend control buttons (`Start Detection`, `Turn Camera OFF`) issue lightweight `POST` requests to `/api/detection/camera/detection/toggle/` and `/api/detection/camera/toggle/` without interrupting the HTTP connection.

---

## 6. Frontend Replacement Compatibility Rules (Lovable AI Readiness)

To allow Lovable AI or any web developer to generate a completely new frontend without touching Python code:

1. **No HTML from Backend**: The backend never generates, parses, or modifies HTML strings.
2. **Self-Descriptive Payloads**: All responses contain complete relational IDs and human-readable names (e.g. `assigned_to: 1`, `assigned_to_name: "John Doe"`).
3. **CORS Headers**: Backend responds to all pre-flight `OPTIONS` requests and sets `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`.
4. **OpenAPI Schema Available**: The backend provides auto-generated OpenAPI 3.0 documentation at `/api/docs/` (Swagger UI) and `/api/schema/` (JSON specification).
5. **Independent Frontend Assets**: Frontend static assets (CSS, JS, logos, icons) are hosted entirely on the frontend dev server (Vite/Node/Vercel) and communicate with the backend solely via HTTP REST APIs.
