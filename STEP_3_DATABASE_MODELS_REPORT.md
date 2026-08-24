# STEP 3: Database Models & ORM Migration Report

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 3 – Database Models and ORM  
**Date**: August 2026  
**Auditor**: Antigravity AI – Advanced Agentic Coding Assistant  
**Status**: COMPLETED & VERIFIED  

---

## 1. Step Objective

The primary objective of **STEP 3** was to migrate the verified legacy SQLite database schema into clean, typed Django ORM models and generate initial Django migrations against the new Django database (`backend/db.sqlite3`). 

In accordance with the strict migration boundaries:
- Zero legacy source files were modified.
- The legacy database (`data.db`) was accessed in strictly read-only mode and remains 100% unaltered.
- Zero API endpoints, CRUD views, serializers, YOLO inference, camera capture, or alert dispatchers were created.

---

## 2. Legacy Database Inspected

- **File Inspected**: `data.db` at workspace root.
- **Access Mode**: Strictly Read-Only (`file:data.db?mode=ro`).
- **Inspection Technique**: SQLite PRAGMA table introspection (`PRAGMA table_info`, `PRAGMA foreign_key_list`, `sqlite_master`).

---

## 3. Legacy Tables Found & Schema Details

| Table | Columns | Row Count | Primary Key | Foreign Keys |
| :--- | :--- | :--- | :--- | :--- |
| `farmers` | `id` (INTEGER), `name` (TEXT), `phone` (TEXT), `field` (TEXT), `email` (TEXT) | 1 | `id` | None |
| `attendance` | `id` (INTEGER), `farmer_id` (INTEGER), `date` (TEXT), `check_in` (TEXT), `check_out` (TEXT), `total_hours` (REAL), `location` (TEXT) | 1 | `id` | `farmer_id` -> `farmers.id` |
| `tasks` | `id` (INTEGER), `task_name` (TEXT), `assigned_to` (INTEGER), `status` (TEXT), `date` (TEXT) | 1 | `id` | `assigned_to` -> `farmers.id` |
| `animal_logs` | `id` (INTEGER), `animal_type` (TEXT), `confidence` (REAL), `timestamp` (TEXT), `field` (TEXT), `image_path` (TEXT) | 2 | `id` | None |
| `alerts` | `id` (INTEGER), `animal_log_id` (INTEGER), `alert_type` (TEXT), `status` (TEXT) | 2 | `id` | `animal_log_id` -> `animal_logs.id` |

---

## 4. Django Apps Created

Five domain applications were created to house the verified models:
1. `backend/apps/farmers/` (`apps.farmers.apps.FarmersConfig`)
2. `backend/apps/attendance/` (`apps.attendance.apps.AttendanceConfig`)
3. `backend/apps/tasks/` (`apps.tasks.apps.TasksConfig`)
4. `backend/apps/detection/` (`apps.detection.apps.DetectionConfig`)
5. `backend/apps/alerts/` (`apps.alerts.apps.AlertsConfig`)

All 5 apps were registered in `INSTALLED_APPS` inside `backend/config/settings.py`.

---

## 5. Django Models Created

### 1. `Farmer` (`apps.farmers.models.Farmer`)
- `name`: `CharField(max_length=150)`
- `phone`: `CharField(max_length=20)`
- `field`: `CharField(max_length=150)`
- `email`: `EmailField(max_length=255, blank=True, null=True)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`

### 2. `Attendance` (`apps.attendance.models.Attendance`)
- `farmer`: `ForeignKey(Farmer, on_delete=CASCADE, related_name='attendances')`
- `date`: `DateField(default=timezone.now)`
- `check_in`: `TimeField(blank=True, null=True)`
- `check_out`: `TimeField(blank=True, null=True)`
- `total_hours`: `FloatField(default=0.0, blank=True, null=True)`
- `location`: `CharField(max_length=255, blank=True, null=True)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`

### 3. `Task` (`apps.tasks.models.Task`)
- `task_name`: `CharField(max_length=255)`
- `assigned_to`: `ForeignKey(Farmer, on_delete=SET_NULL, blank=True, null=True, related_name='tasks')`
- `status`: `CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')`
- `date`: `DateField(default=timezone.now)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`

### 4. `AnimalLog` (`apps.detection.models.AnimalLog`)
- `animal_type`: `CharField(max_length=100)`
- `confidence`: `FloatField(blank=True, null=True)`
- `timestamp`: `DateTimeField(default=timezone.now)`
- `field`: `CharField(max_length=150, default='Main Field')`
- `image_path`: `CharField(max_length=255)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`

### 5. `Alert` (`apps.alerts.models.Alert`)
- `animal_log`: `ForeignKey(AnimalLog, on_delete=CASCADE, blank=True, null=True, related_name='alerts')`
- `alert_type`: `CharField(max_length=50)` # e.g. 'Email + Buzzer', 'Email', 'Log Only'
- `status`: `CharField(max_length=30, default='Triggered')`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `updated_at`: `DateTimeField(auto_now=True)`

---

## 6. Field Mapping Summary

- `TEXT` date and time strings (e.g. `'2026-08-24'`, `'08:30:00'`) were mapped to native Django `DateField` and `TimeField` for query optimization and date arithmetic.
- `TEXT` timestamps were mapped to native `DateTimeField(default=timezone.now)`.
- Added standard timestamp audit fields (`created_at`, `updated_at`) to all models.

---

## 7. Relationship Decisions

- **`Attendance.farmer`**: `on_delete=models.CASCADE` ensures attendance records are tied to their parent farmer.
- **`Task.assigned_to`**: `on_delete=models.SET_NULL, null=True` allows unassigning tasks if a worker record is removed without losing the task record.
- **`Alert.animal_log`**: `on_delete=models.CASCADE, null=True` links the alert directly to the triggering vision log.

---

## 8. Intentional Redesign Decisions

1. **Native Typing**: Replaced raw string representations with native `DateField`, `TimeField`, `DateTimeField`, and `EmailField` objects.
2. **Explicit ForeignKey Constraints**: Replaced raw integer IDs (`assigned_to INTEGER`, `farmer_id INTEGER`, `animal_log_id INTEGER`) with proper Django ORM `ForeignKey` relationships.
3. **Auditability**: Added `created_at` and `updated_at` to every model.

---

## 9. Django Migration Files Created

- `backend/apps/farmers/migrations/0001_initial.py`
- `backend/apps/attendance/migrations/0001_initial.py`
- `backend/apps/tasks/migrations/0001_initial.py`
- `backend/apps/detection/migrations/0001_initial.py`
- `backend/apps/alerts/migrations/0001_initial.py`

---

## 10. Database Commands Executed

```powershell
# 1. Check model configuration
python manage.py check

# 2. Generate migration files
python manage.py makemigrations

# 3. Verify no uncommitted migrations
python manage.py makemigrations --check

# 4. Apply migrations to Django SQLite database
python manage.py migrate

# 5. Run automated test suite
python manage.py test
```

---

## 11. Verification Results

- **System Check**: `System check identified no issues (0 silenced).` (PASS)
- **Migrations Check**: `No changes detected.` (PASS)
- **Migrate Output**: `Applying detection.0001_initial... OK`, `alerts.0001_initial... OK`, `farmers.0001_initial... OK`, `attendance.0001_initial... OK`, `tasks.0001_initial... OK`. (PASS)
- **Unit Tests**: `Ran 8 tests in 0.039s - OK` (PASS)

---

## 12. Automated Tests Summary

1. `apps.core.tests`: 3 tests (Health check, API root, 404 formatting).
2. `apps.farmers.tests`: 1 test (`Farmer` model creation, string representation).
3. `apps.attendance.tests`: 1 test (`Attendance` model creation, FK relation).
4. `apps.tasks.tests`: 1 test (`Task` model creation, status choices).
5. `apps.detection.tests`: 1 test (`AnimalLog` model creation, confidence score).
6. `apps.alerts.tests`: 1 test (`Alert` model creation, FK relation to `AnimalLog`).

---

## 13. Legacy Database Modification Status

- **Status**: **100% UNMODIFIED & UNTOUCHED**.
- Verified read-only row counts before and after migration:
  - `farmers`: 1
  - `attendance`: 1
  - `tasks`: 1
  - `animal_logs`: 2
  - `alerts`: 2

---

## 14. Data Import Status

- Legacy data was **NOT** imported. (Schema migration only, as required).

---

## 15. Features Intentionally Not Migrated

- Serializers and API ViewSets (`Steps 5–13`).
- User accounts and JWT Authentication (`Step 4`).
- YOLOv8 inference service (`Step 10`).
- Camera capture and streaming (`Step 11`).
- Email and buzzer notification service (`Step 13`).
- Frontend UI components (`Step 15`).

---

## 16. Known Limitations

- The new database schema is initialized and tested with empty tables; data migration scripts or seed fixtures will be applied as needed in future steps.

---

## 17. Risks Found

- None. All 5 domain models mapped cleanly from SQLite tables to Django ORM without constraint conflicts.

---

## 18. Step 3 Completion Checklist

- [x] Legacy SQLite database (`data.db`) inspected read-only.
- [x] All 5 legacy tables verified against Step 0 findings.
- [x] 5 domain apps created (`farmers`, `attendance`, `tasks`, `detection`, `alerts`).
- [x] All models defined with typed fields, foreign keys, and string representations.
- [x] All 5 apps registered in `INSTALLED_APPS`.
- [x] Minimal admin registration added for development convenience.
- [x] `makemigrations` executed and initial migration files generated.
- [x] `migrate` executed against `backend/db.sqlite3`.
- [x] Automated unit test suite executed (8/8 tests passed).
- [x] Documentation deliverable `docs/architecture/database_schema_step_3.md` created.
- [x] Step 3 report `STEP_3_DATABASE_MODELS_REPORT.md` generated.
- [x] Git rule upheld: Zero git commit or push commands executed.

---

## REVIEWER HANDOFF

**Legacy Project Modified:**  
`NO`

**Legacy Database Modified:**  
`NO`

**Legacy Database Used Read-Only:**  
`YES`

**Django Models Created:**  
- `Farmer` (`apps.farmers.models.Farmer`)
- `Attendance` (`apps.attendance.models.Attendance`)
- `Task` (`apps.tasks.models.Task`)
- `AnimalLog` (`apps.detection.models.AnimalLog`)
- `Alert` (`apps.alerts.models.Alert`)

**Django Migrations Applied:**  
`YES` (Applied to `backend/db.sqlite3`)

**Django System Check:**  
`PASS`

**Model Tests:**  
`PASS` (8/8 tests passed)

**Legacy Data Imported:**  
`NO`

**API CRUD Implemented:**  
`NO`

**YOLO Migrated:**  
`NO`

**Camera Migrated:**  
`NO`

**Alerts Migrated:**  
`NO`

**Recommended Next Step:**  
`STEP 4 - Authentication and Authorization`
