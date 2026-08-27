# FarmSync Tasks Management REST API Specification (Step 9)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 9 – Tasks Management REST APIs  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Step Objective & Architectural Boundary

The **Tasks Module** (`apps.tasks`) provides a decoupled, secure, and production-ready RESTful API for assigning, tracking, filtering, and updating agricultural work tasks delegated to farm workers.

### Core Architectural Decisions:
1. **Model Reuse**: Operates on the existing `Task` model (`backend/apps/tasks/models.py`) created in Step 3. Zero model schema modifications or database migrations were required.
2. **Frontend Independence**: Decoupled JSON API conforming strictly to the unified FarmSync response envelope (`success`, `message`, `data`/`errors`), ready for modern Single Page Applications (SPAs), mobile apps, or Lovable AI-generated interfaces.
3. **Role-Based Authorization**: Leverages `IsAdminOrReadOnly` to permit regular workers to read task lists and details, while restricting task creation, full editing (PUT), partial updates (PATCH), and task deletion strictly to staff and administrators.
4. **Relational Integrity**: Maintains foreign key linkage to `Farmer` with `on_delete=models.SET_NULL`, ensuring historical task records remain intact with `assigned_to = NULL` if an assigned farm worker is removed.

---

## 2. Legacy Evidence Audit & Classification Matrix

| Behavior | Verified Legacy Behavior | Concrete Evidence | Classification |
|---|---|---|---|
| **Task Creation** | Form POST with `task_name` and `assigned_to` inserting into SQLite `tasks` table with default `Pending` status and current date. | `modules/tasks.py` lines 4-7; `app.py` lines 101-107; `templates/tasks.html` lines 35-45 | **LEGACY-VERIFIED** |
| **Required Fields** | `task_name` (non-null/required) and `assigned_to` (required in legacy HTML form). `date` automatically set to `YYYY-MM-DD`. | `database/db.py` line 41; `templates/tasks.html` lines 36-37; `modules/tasks.py` line 5 | **LEGACY-VERIFIED** |
| **Blank Task Name** | Rejected; form input marked `required`, and backend `if task_name and assigned_to:`. | `templates/tasks.html` line 36; `app.py` line 105 | **LEGACY-VERIFIED** |
| **Assigned Worker FK** | `assigned_to` stores `farmers.id` foreign key. Form rendered from `SELECT * FROM farmers`. | `database/db.py` lines 42, 45; `modules/tasks.py` line 15; `templates/tasks.html` lines 39-41 | **LEGACY-VERIFIED** |
| **Default Status** | `Pending` upon creation. | `modules/tasks.py` line 6 (`'Pending'`); `backend/apps/tasks/models.py` line 28 | **LEGACY-VERIFIED** |
| **Verified Statuses** | Only `'Pending'` and `'Completed'` exist in legacy code and data. | `modules/tasks.py` line 6; `templates/tasks.html` lines 60, 62, 65; `app.py` line 39; `data.db` row 1 (`'Completed'`) | **LEGACY-VERIFIED** |
| **Task Completion** | POST `/update_task` sets status to `'Completed'`. | `modules/tasks.py` line 9-10; `app.py` lines 109-115; `templates/tasks.html` lines 63-67 | **LEGACY-VERIFIED** |
| **Task Editing (PUT/PATCH)** | Legacy only supported updating status. Full task editing (updating name, worker, date) did not exist. | `modules/tasks.py` (only `update_task_status`); `app.py` (only `/update_task`) | **DJANGO/API ENHANCEMENT** |
| **Task Deletion** | No delete functionality in legacy application. | Absence in `modules/tasks.py`, `app.py`, `templates/tasks.html` | **DJANGO/API ENHANCEMENT** |
| **Task Listing & Ordering** | Reverse ID order (`ORDER BY t.id DESC`). | `modules/tasks.py` line 16; `backend/apps/tasks/models.py` line 36 | **LEGACY-VERIFIED** |
| **Filtering (Status, Worker, Date)** | Legacy had no filter controls in task list view. | `modules/tasks.py` `get_all_tasks()` returned all rows without WHERE clause. | **DJANGO/API ENHANCEMENT** |
| **Unassigned Tasks / Null Farmer** | Schema allowed NULL `assigned_to` (`INTEGER` without `NOT NULL`), but UI form required farmer selection. Django model uses `models.SET_NULL, null=True, blank=True`. | `database/db.py` line 42; `backend/apps/tasks/models.py` lines 17-24 | **LEGACY-VERIFIED / DJANGO ENHANCEMENT** |
| **Worker Deletion Effect** | In Django model, `on_delete=models.SET_NULL` preserves task history with `assigned_to=NULL`. | `backend/apps/tasks/models.py` line 19; verified by automated tests | **LEGACY-VERIFIED (Model Schema)** |

---

## 3. Model & Relational Cascades

### 3.1 Model Fields (`apps.tasks.models.Task`)
- `id`: AutoField (Read-only primary key).
- `task_name`: CharField (max 255, required, sanitized against blank and whitespace-only values).
- `assigned_to`: ForeignKey to `farmers.Farmer` (`on_delete=models.SET_NULL`, nullable, blankable, related_name=`tasks`).
- `status`: CharField (max 20, choices: `Pending`, `Completed`, default=`Pending`).
- `date`: DateField (default=`timezone.now`, formatted as `YYYY-MM-DD`).
- `created_at`: DateTimeField (Read-only auto timestamp).
- `updated_at`: DateTimeField (Read-only auto timestamp).

---

## 4. Endpoints Reference

All endpoints are mounted under `/api/v1/tasks/`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/tasks/` | Authenticated | Lists all tasks with optional filters (`status`, `assigned_to`/`farmer_id`, `date`, `start_date`, `end_date`) ordered by `-id`. |
| `POST` | `/api/v1/tasks/` | Staff / Admin | Creates a new task assignment. |
| `GET` | `/api/v1/tasks/{id}/` | Authenticated | Retrieves detailed record of a specific task. |
| `PUT` | `/api/v1/tasks/{id}/` | Staff / Admin | Performs a full update of all task fields. |
| `PATCH` | `/api/v1/tasks/{id}/` | Staff / Admin | Performs a partial update (e.g. status transition, reassignment). |
| `DELETE` | `/api/v1/tasks/{id}/` | Staff / Admin | Deletes a task record. |

---

## 5. Request & Response Examples

### 5.1 List Tasks (`GET /api/v1/tasks/?status=Pending`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Tasks retrieved successfully.",
    "data": [
      {
        "id": 1,
        "task_name": "Check drip irrigation lines",
        "assigned_to": 1,
        "assigned_to_name": "Alice Smith",
        "status": "Pending",
        "date": "2026-08-24",
        "created_at": "2026-08-24T12:00:00Z",
        "updated_at": "2026-08-24T12:00:00Z"
      }
    ]
  }
  ```

---

### 5.2 Create Task (`POST /api/v1/tasks/`)
- **Request**:
  ```json
  {
    "task_name": "Repair greenhouse ventilation",
    "assigned_to": 1,
    "status": "Pending"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "success": true,
    "message": "Task created successfully.",
    "data": {
      "id": 2,
      "task_name": "Repair greenhouse ventilation",
      "assigned_to": 1,
      "assigned_to_name": "Alice Smith",
      "status": "Pending",
      "date": "2026-08-24",
      "created_at": "2026-08-24T14:30:00Z",
      "updated_at": "2026-08-24T14:30:00Z"
    }
  }
  ```

---

### 5.3 Partial Update / Complete Task (`PATCH /api/v1/tasks/{id}/`)
- **Request**:
  ```json
  {
    "status": "Completed"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Task partially updated successfully.",
    "data": {
      "id": 2,
      "task_name": "Repair greenhouse ventilation",
      "assigned_to": 1,
      "assigned_to_name": "Alice Smith",
      "status": "Completed",
      "date": "2026-08-24",
      "created_at": "2026-08-24T14:30:00Z",
      "updated_at": "2026-08-24T14:45:00Z"
    }
  }
  ```

---

### 5.4 Delete Task (`DELETE /api/v1/tasks/{id}/`)
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Task deleted successfully.",
    "data": {}
  }
  ```

---

## 6. Authorization Policy & Security

1. **Unauthenticated Access**: Rejected with `401 Unauthorized` on all endpoints.
2. **Regular Authenticated Users**: Read access (`GET /api/v1/tasks/` and `GET /api/v1/tasks/{id}/`) permitted; write actions (`POST`, `PUT`, `PATCH`, `DELETE`) are strictly rejected with `403 Forbidden`.
3. **Staff & Administrators**: Full read, create, update, and delete access.
4. **Validation Rules**:
   - Blank or whitespace-only `task_name` rejected with `400 Bad Request`.
   - Nonexistent `assigned_to` foreign key rejected with `400 Bad Request`.
   - Invalid `status` choices rejected with `400 Bad Request` (only `'Pending'` and `'Completed'` permitted).
   - PATCH preserves all unspecified fields.
