# FarmSync Farmers CRUD API Specification (Step 7)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 7 – Farmers CRUD REST APIs  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Step Objective & Architectural Boundary

The **Farmers Module** (`apps.farmers`) provides a secure, production-quality RESTful CRUD API layer for managing agricultural workforce personnel.

### Core Architectural Decisions:
1. **Model Reuse**: Operates on the existing `Farmer` model (`backend/apps/farmers/models.py`) created in Step 3. Zero model modifications or database migrations were required.
2. **Frontend Independence**: Fully decoupled API returning standard JSON envelopes, ready to be consumed by the legacy template frontend, modern React/Vue SPAs, or Lovable AI-generated interfaces.
3. **Role-Based Authorization**: Uses `IsAdminOrReadOnly` to permit regular workers to read workforce rosters while reserving creation, updates, and deletions strictly for farm administrators and staff.

---

## 2. Model & Relational Cascades

### 2.1 Model Fields (`apps.farmers.models.Farmer`)
- `id`: AutoField (Read-only, primary key).
- `name`: CharField (max 150, required, trimmed non-empty).
- `phone`: CharField (max 20, required, trimmed non-empty).
- `field`: CharField (max 150, required, assigned sector/location).
- `email`: EmailField (max 255, optional/nullable).
- `created_at`: DateTimeField (Read-only auto timestamp).
- `updated_at`: DateTimeField (Read-only auto timestamp).

### 2.2 Foreign Key Delete Behavior
1. **`Attendance.farmer` (`on_delete=models.CASCADE`)**:
   - Deleting a `Farmer` will cascade-delete their associated `Attendance` logs.
2. **`Task.assigned_to` (`on_delete=models.SET_NULL, null=True`)**:
   - Deleting a `Farmer` automatically updates their associated `Task` records to have `assigned_to = NULL`, preserving task history.

---

## 3. Endpoints Reference

All endpoints are mounted under `/api/v1/farmers/`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/farmers/` | Authenticated | Lists all farmers ordered alphabetically (`name`, `id`). |
| `POST` | `/api/v1/farmers/` | Staff / Admin | Registers a new farm worker. |
| `GET` | `/api/v1/farmers/{id}/` | Authenticated | Retrieves details of a specific farmer. |
| `PUT` | `/api/v1/farmers/{id}/` | Staff / Admin | Performs a full update of all farmer fields. |
| `PATCH` | `/api/v1/farmers/{id}/` | Staff / Admin | Performs a partial update (unspecified fields preserved). |
| `DELETE` | `/api/v1/farmers/{id}/` | Staff / Admin | Deletes a farmer record (cascades to attendance, sets task assignee null). |

---

## 4. Request & Response Examples

### 4.1 List Farmers (`GET /api/v1/farmers/`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Farmers retrieved successfully.",
    "data": [
      {
        "id": 1,
        "name": "Alice Smith",
        "phone": "1234567890",
        "field": "North Field",
        "email": "alice@example.com",
        "created_at": "2026-08-24T12:00:00Z",
        "updated_at": "2026-08-24T12:00:00Z"
      }
    ]
  }
  ```

---

### 4.2 Create Farmer (`POST /api/v1/farmers/`)
- **Request**:
  ```json
  {
    "name": "Charlie Green",
    "phone": "555-1234",
    "field": "Greenhouse A",
    "email": "charlie@farmsync.org"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "success": true,
    "message": "Farmer created successfully.",
    "data": {
      "id": 2,
      "name": "Charlie Green",
      "phone": "555-1234",
      "field": "Greenhouse A",
      "email": "charlie@farmsync.org",
      "created_at": "2026-08-24T13:00:00Z",
      "updated_at": "2026-08-24T13:00:00Z"
    }
  }
  ```

---

### 4.3 Partial Update (`PATCH /api/v1/farmers/{id}/`)
- **Request**:
  ```json
  {
    "field": "Greenhouse B"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Farmer partially updated successfully.",
    "data": {
      "id": 2,
      "name": "Charlie Green",
      "phone": "555-1234",
      "field": "Greenhouse B",
      "email": "charlie@farmsync.org",
      "created_at": "2026-08-24T13:00:00Z",
      "updated_at": "2026-08-24T13:05:00Z"
    }
  }
  ```

---

### 4.4 Delete Farmer (`DELETE /api/v1/farmers/{id}/`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Farmer deleted successfully.",
    "data": {}
  }
  ```

---

## 5. Legacy Feature Mapping

| Legacy Capability | Legacy Source File | Django API Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **View Farmers Roster** | `app.py` line 140 (`/farmers`), `templates/farmers.html` | `GET /api/v1/farmers/` | **MIGRATED & ENHANCED** |
| **Add New Farmer** | `app.py` line 145 (`/add_farmer`), `templates/farmers.html` | `POST /api/v1/farmers/` | **MIGRATED & ENHANCED** |
| **Delete Farmer** | `app.py` line 156 (`/delete_farmer/<int:id>`) | `DELETE /api/v1/farmers/{id}/` | **MIGRATED & ENHANCED** |
| **Get Single Farmer** | Not available in legacy Flask | `GET /api/v1/farmers/{id}/` | **NEW DJANGO ENHANCEMENT** |
| **Full Update (PUT)** | Not available in legacy Flask | `PUT /api/v1/farmers/{id}/` | **NEW DJANGO ENHANCEMENT** |
| **Partial Update (PATCH)** | Not available in legacy Flask | `PATCH /api/v1/farmers/{id}/` | **NEW DJANGO ENHANCEMENT** |

---

## 6. Authorization Policy & Security

1. **Unauthenticated Access**: Rejected with `401 Unauthorized` on all endpoints.
2. **Regular Authenticated Users**: Read access (`GET /api/v1/farmers/` and `GET /api/v1/farmers/{id}/`) allowed; write operations (`POST`, `PUT`, `PATCH`, `DELETE`) are rejected with `403 Forbidden`.
3. **Staff & Superusers**: Full read and write access.
4. **Input Validation**: Server-side serializer validation on all fields; whitespace-only strings rejected with `400 Bad Request`.
