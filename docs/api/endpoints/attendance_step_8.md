# FarmSync Attendance Module API Specification (Step 8)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 8 – Attendance Action & Analytical REST APIs  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Objective & Architectural Boundary

The **Attendance Module** (`apps.attendance`) provides an authenticated, RESTful API layer for worker check-in, check-out, duration calculation, and analytical reporting.

### Core Architectural Decisions:
1. **Model Reuse**: Reuses the existing `Attendance` model (`backend/apps/attendance/models.py`) created in Step 3. Zero model modifications or database migrations were required.
2. **Domain Action Workflow**: Preserves the event-driven workflow of check-in and check-out rather than exposing arbitrary update endpoints.
3. **Decoupled Frontend Consumption**: Returns standard JSON API response envelopes compatible with the legacy template frontend, modern React/Vue SPAs, or Lovable AI-generated client interfaces.

---

## 2. Legacy Attendance Evidence Audit

| Audit Question | Verified Legacy Behavior | Concrete Evidence Source |
| :--- | :--- | :--- |
| **A. Check-in Execution** | Inserts `(farmer_id, date, check_in_time, NULL, 0.0, location)` if no record exists for that farmer today. | `modules/attendance.py` line 31 (`mark_check_in()`) |
| **B. Check-out Execution** | Finds open record (`check_out IS NULL`) for today, computes duration, and updates record with `check_out_time` and `total_hours`. | `modules/attendance.py` line 54 (`mark_check_out()`) |
| **C. Multiple Records per Date** | Strictly restricted to 1 record per farmer per date (`SELECT * WHERE farmer_id = ? AND date = ?`). | `modules/attendance.py` line 46-47 |
| **D. Duplicate Check-in Handling** | Rejected if a record already exists for the farmer on the target date. | `modules/attendance.py` line 47, 52 |
| **E. Check-out Matching** | Matches open attendance record by `farmer_id` and target `date`. | `modules/attendance.py` line 69-70 |
| **F. Total Hours Calculation** | Formula: `(check_out_time - check_in_time).total_seconds() / 3600.0`, rounded to 2 decimal places (`round(hours, 2)`). | `modules/attendance.py` lines 71-75 |
| **G. Total Hours Timing** | Calculated dynamically during check-out. | `modules/attendance.py` line 77 |
| **H. Date Format** | `YYYY-MM-DD` (e.g. `2026-08-24`). | `modules/attendance.py` line 32 (`strftime("%Y-%m-%d")`) |
| **I. Time Format** | `HH:MM:SS` (e.g. `08:30:00`). | `modules/attendance.py` line 33 (`strftime("%H:%M:%S")`) |
| **J. Location Handling** | Optional device location passed by client (e.g. `"12.9716, 77.5946"`), falling back to `farmer.field`. | `modules/attendance.py` line 39, `templates/attendance.html` line 94 |
| **K. Location Requirement** | Optional. Default fallback is `farmer.field`. | `modules/attendance.py` line 39 |
| **L. Geolocation Validation** | Stored as generic string (max 255 chars) without strict format restriction. | `database/db.py`, `models.py` |
| **M. Check-out without Check-in** | Fails and returns validation error. | `modules/attendance.py` line 70, 80 |
| **N. Repeated Check-in** | Fails and returns validation error indicating record already exists today. | `modules/attendance.py` line 47, 52 |
| **O. Attendance Reports** | Filter logs by `start_date` and `end_date`, ordering by date and check-in descending. | `app.py` lines 117-137 (`/attendance_report`) |
| **P. Report Calculations** | Aggregates logs, counts records, and computes total hours logged across the date range. | `app.py` line 124, `templates/attendance_report.html` |
| **Q. Wage Calculation** | **NOT performed or displayed** in legacy attendance. `wage_per_hour` existed in `config.json` but was never referenced in attendance routes. Documented as not included. | `modules/attendance.py`, `app.py`, `attendance_report.html` |

---

## 3. Endpoints Reference

All endpoints are mounted under `/api/v1/attendance/`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/attendance/` | Authenticated | Lists attendance records (supports `farmer_id`, `date`, `start_date`, `end_date`, `is_active`). |
| `GET` | `/api/v1/attendance/{id}/` | Authenticated | Retrieves single attendance log details. |
| `POST` | `/api/v1/attendance/check-in/` | Staff / Admin | Records worker check-in (validates existence and prevents duplicate check-in). |
| `POST` | `/api/v1/attendance/check-out/` | Staff / Admin | Records worker check-out and computes duration in decimal hours. |
| `GET` | `/api/v1/attendance/report/` | Authenticated | Generates structured attendance reports with date range filtering. |

---

## 4. Request & Response Examples

### 4.1 Check-In (`POST /api/v1/attendance/check-in/`)
- **Request**:
  ```json
  {
    "farmer_id": 1,
    "device_location": "12.9716, 77.5946",
    "check_in_time": "08:00:00",
    "date": "2026-08-24"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "success": true,
    "message": "Worker check-in recorded successfully.",
    "data": {
      "id": 10,
      "farmer": 1,
      "farmer_name": "John Doe",
      "date": "2026-08-24",
      "check_in": "08:00:00",
      "check_out": null,
      "total_hours": 0.0,
      "location": "12.9716, 77.5946",
      "created_at": "2026-08-24T08:00:00Z",
      "updated_at": "2026-08-24T08:00:00Z"
    }
  }
  ```

---

### 4.2 Check-Out (`POST /api/v1/attendance/check-out/`)
- **Request**:
  ```json
  {
    "farmer_id": 1,
    "check_out_time": "16:30:00"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Worker check-out recorded successfully.",
    "data": {
      "id": 10,
      "farmer": 1,
      "farmer_name": "John Doe",
      "date": "2026-08-24",
      "check_in": "08:00:00",
      "check_out": "16:30:00",
      "total_hours": 8.5,
      "location": "12.9716, 77.5946",
      "created_at": "2026-08-24T08:00:00Z",
      "updated_at": "2026-08-24T16:30:00Z"
    }
  }
  ```

---

### 4.3 Attendance Report (`GET /api/v1/attendance/report/?start_date=2026-08-01&end_date=2026-08-31`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Attendance report generated successfully.",
    "data": {
      "start_date": "2026-08-01",
      "end_date": "2026-08-31",
      "farmer_id": null,
      "total_records": 1,
      "total_hours_sum": 8.5,
      "records": [
        {
          "id": 10,
          "farmer": 1,
          "farmer_name": "John Doe",
          "date": "2026-08-24",
          "check_in": "08:00:00",
          "check_out": "16:30:00",
          "total_hours": 8.5,
          "location": "12.9716, 77.5946",
          "created_at": "2026-08-24T08:00:00Z",
          "updated_at": "2026-08-24T16:30:00Z"
        }
      ]
    }
  }
  ```

---

## 5. Legacy Feature Mapping

| Legacy Capability | Legacy Source File | Django API Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **View Attendance Logs** | `app.py` line 84, `templates/attendance.html` | `GET /api/v1/attendance/` | **MIGRATED & ENHANCED** |
| **Worker Check-In** | `app.py` line 84 (`/check_in`), `modules/attendance.py` line 31 | `POST /api/v1/attendance/check-in/` | **MIGRATED & ENHANCED** |
| **Worker Check-Out** | `app.py` line 92 (`/check_out`), `modules/attendance.py` line 54 | `POST /api/v1/attendance/check-out/` | **MIGRATED & ENHANCED** |
| **Attendance Report** | `app.py` line 117 (`/attendance_report`), `templates/attendance_report.html` | `GET /api/v1/attendance/report/` | **MIGRATED & ENHANCED** |
| **Single Log Detail** | Not available in legacy Flask | `GET /api/v1/attendance/{id}/` | **NEW DJANGO ENHANCEMENT** |
| **Active / Open Filter** | Not available in legacy Flask | `GET /api/v1/attendance/?is_active=true` | **NEW DJANGO ENHANCEMENT** |

---

## 6. Authorization Policy & Security

1. **Unauthenticated Access**: Rejected with `401 Unauthorized`.
2. **Regular Authenticated Users**: Read access (`GET` list, detail, report) allowed; write operations (`POST` check-in, check-out) rejected with `403 Forbidden`.
3. **Staff & Superusers**: Full access (`IsAdminOrReadOnly`).
4. **Server-Side Validation**: Validates date ranges, prevents start_date > end_date, validates farmer existence, prevents duplicate check-ins on the same day.
