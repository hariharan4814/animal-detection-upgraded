# FarmSync Database Schema Specification & Migration Blueprint (Step 3)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 3 – Database Models & ORM Migration  
**Date**: August 2026  
**Status**: COMPLETED & VERIFIED  

---

## 1. Legacy Database Summary & Inspection

A complete, read-only inspection was performed directly against the legacy SQLite database (`data.db`) using SQLite PRAGMA introspection tools and source code cross-referencing.

### 1.1 Verified Table Inventory & Row Counts

| Legacy Table Name | Verified Columns | Row Count | Primary Key | Foreign Keys | Migration Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `farmers` | `id`, `name`, `phone`, `field`, `email` | 1 | `id` (INTEGER AUTOINCREMENT) | None | **CLEAN MAPPING** |
| `attendance` | `id`, `farmer_id`, `date`, `check_in`, `check_out`, `total_hours`, `location` | 1 | `id` (INTEGER AUTOINCREMENT) | `farmer_id` -> `farmers(id)` | **CLEAN MAPPING** |
| `tasks` | `id`, `task_name`, `assigned_to`, `status`, `date` | 1 | `id` (INTEGER AUTOINCREMENT) | `assigned_to` -> `farmers(id)` | **CLEAN MAPPING** |
| `animal_logs` | `id`, `animal_type`, `confidence`, `timestamp`, `field`, `image_path` | 2 | `id` (INTEGER AUTOINCREMENT) | None | **CLEAN MAPPING** |
| `alerts` | `id`, `animal_log_id`, `alert_type`, `status` | 2 | `id` (INTEGER AUTOINCREMENT) | `animal_log_id` -> `animal_logs(id)` | **CLEAN MAPPING** |

---

## 2. Entity Mapping & Django Models

### 2.1 Entity 1: Farmers (`apps.farmers.models.Farmer`)
- **Django App**: `apps.farmers`
- **Model Name**: `Farmer`
- **Table Name**: `farmers_farmer` (Django default)

#### Field Mapping
| Legacy SQLite Column | Legacy Type | Django ORM Field | Nullable | Constraints & Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER PK | `BigAutoField` | No | Primary key |
| `name` | TEXT NOT NULL | `CharField(max_length=150)` | No | Full worker name |
| `phone` | TEXT NOT NULL | `CharField(max_length=20)` | No | Contact phone number |
| `field` | TEXT NOT NULL | `CharField(max_length=150)` | No | Assigned field/area |
| `email` | TEXT | `EmailField(max_length=255)` | Yes | Optional email address for notifications |
| *(New in Django)* | - | `created_at = DateTimeField(auto_now_add=True)` | No | Auto-timestamp |
| *(New in Django)* | - | `updated_at = DateTimeField(auto_now=True)` | No | Auto-timestamp |

---

### 2.2 Entity 2: Attendance (`apps.attendance.models.Attendance`)
- **Django App**: `apps.attendance`
- **Model Name**: `Attendance`
- **Table Name**: `attendance_attendance` (Django default)

#### Field Mapping
| Legacy SQLite Column | Legacy Type | Django ORM Field | Nullable | Constraints & Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER PK | `BigAutoField` | No | Primary key |
| `farmer_id` | INTEGER NOT NULL | `ForeignKey('farmers.Farmer', on_delete=CASCADE, related_name='attendances')` | No | Reference to worker |
| `date` | TEXT NOT NULL | `DateField(default=timezone.now)` | No | Attendance date (YYYY-MM-DD) |
| `check_in` | TEXT | `TimeField(blank=True, null=True)` | Yes | Check-in time |
| `check_out` | TEXT | `TimeField(blank=True, null=True)` | Yes | Check-out time |
| `total_hours` | REAL | `FloatField(default=0.0, blank=True, null=True)` | Yes | Duration in decimal hours |
| `location` | TEXT | `CharField(max_length=255, blank=True, null=True)` | Yes | GPS coordinates or location name |
| *(New in Django)* | - | `created_at = DateTimeField(auto_now_add=True)` | No | Auto-timestamp |
| *(New in Django)* | - | `updated_at = DateTimeField(auto_now=True)` | No | Auto-timestamp |

---

### 2.3 Entity 3: Tasks (`apps.tasks.models.Task`)
- **Django App**: `apps.tasks`
- **Model Name**: `Task`
- **Table Name**: `tasks_task` (Django default)

#### Field Mapping
| Legacy SQLite Column | Legacy Type | Django ORM Field | Nullable | Constraints & Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER PK | `BigAutoField` | No | Primary key |
| `task_name` | TEXT NOT NULL | `CharField(max_length=255)` | No | Task description |
| `assigned_to` | INTEGER | `ForeignKey('farmers.Farmer', on_delete=SET_NULL, blank=True, null=True, related_name='tasks')` | Yes | Assigned worker |
| `status` | TEXT NOT NULL | `CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')` | No | Task status |
| `date` | TEXT NOT NULL | `DateField(default=timezone.now)` | No | Assignment date |
| *(New in Django)* | - | `created_at = DateTimeField(auto_now_add=True)` | No | Auto-timestamp |
| *(New in Django)* | - | `updated_at = DateTimeField(auto_now=True)` | No | Auto-timestamp |

---

### 2.4 Entity 4: Animal Logs (`apps.detection.models.AnimalLog`)
- **Django App**: `apps.detection`
- **Model Name**: `AnimalLog`
- **Table Name**: `detection_animallog` (Django default)

#### Field Mapping
| Legacy SQLite Column | Legacy Type | Django ORM Field | Nullable | Constraints & Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER PK | `BigAutoField` | No | Primary key |
| `animal_type` | TEXT NOT NULL | `CharField(max_length=100)` | No | Animal species class |
| `confidence` | REAL | `FloatField(blank=True, null=True)` | Yes | Detection confidence (0.0–1.0) |
| `timestamp` | TEXT NOT NULL | `DateTimeField(default=timezone.now)` | No | Detection timestamp |
| `field` | TEXT NOT NULL | `CharField(max_length=150, default='Main Field')` | No | Camera field location |
| `image_path` | TEXT NOT NULL | `CharField(max_length=255)` | No | Relative path to image snapshot |
| *(New in Django)* | - | `created_at = DateTimeField(auto_now_add=True)` | No | Auto-timestamp |
| *(New in Django)* | - | `updated_at = DateTimeField(auto_now=True)` | No | Auto-timestamp |

---

### 2.5 Entity 5: Alerts (`apps.alerts.models.Alert`)
- **Django App**: `apps.alerts`
- **Model Name**: `Alert`
- **Table Name**: `alerts_alert` (Django default)

#### Field Mapping
| Legacy SQLite Column | Legacy Type | Django ORM Field | Nullable | Constraints & Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER PK | `BigAutoField` | No | Primary key |
| `animal_log_id` | INTEGER | `ForeignKey('detection.AnimalLog', on_delete=CASCADE, blank=True, null=True, related_name='alerts')` | Yes | Parent detection log |
| `alert_type` | TEXT NOT NULL | `CharField(max_length=50)` | No | 'Email + Buzzer', 'Email', 'Log Only' |
| `status` | TEXT NOT NULL | `CharField(max_length=30, default='Triggered')` | No | 'Triggered', 'Sent', etc. |
| *(New in Django)* | - | `created_at = DateTimeField(auto_now_add=True)` | No | Auto-timestamp |
| *(New in Django)* | - | `updated_at = DateTimeField(auto_now=True)` | No | Auto-timestamp |

---

## 3. Raw SQL vs. Django ORM Comparison

| Operation | Legacy Flask SQL Pattern | New Django ORM Pattern |
| :--- | :--- | :--- |
| **Total Farmers** | `SELECT COUNT(*) FROM farmers` | `Farmer.objects.count()` |
| **Today's Attendance** | `SELECT COUNT(*) FROM attendance WHERE date = ?` | `Attendance.objects.filter(date=today).count()` |
| **Attendance Report** | `SELECT a.id, f.name... FROM attendance a JOIN farmers f ON a.farmer_id = f.id WHERE a.date >= ? AND a.date <= ?` | `Attendance.objects.select_related('farmer').filter(date__range=(start, end))` |
| **Recent Detection Logs** | `SELECT * FROM animal_logs ORDER BY timestamp DESC LIMIT 50` | `AnimalLog.objects.all()[:50]` |
| **Active Alerts** | `SELECT a.id, al.animal_type... FROM alerts a JOIN animal_logs al ON a.animal_log_id = al.id` | `Alert.objects.select_related('animal_log').all()[:10]` |
| **Pending Tasks** | `SELECT * FROM tasks WHERE status = 'Completed'` | `Task.objects.filter(status='Completed')` |

---

## 4. Generated Django Migration Files

1. `backend/apps/farmers/migrations/0001_initial.py` (Creates `Farmer`)
2. `backend/apps/attendance/migrations/0001_initial.py` (Creates `Attendance` with FK to `Farmer`)
3. `backend/apps/tasks/migrations/0001_initial.py` (Creates `Task` with FK to `Farmer`)
4. `backend/apps/detection/migrations/0001_initial.py` (Creates `AnimalLog`)
5. `backend/apps/alerts/migrations/0001_initial.py` (Creates `Alert` with FK to `AnimalLog`)

---

## 5. Verification Summary

- `python manage.py check`: PASSED (0 issues).
- `python manage.py makemigrations --check`: PASSED (No uncommitted model changes).
- `python manage.py migrate`: PASSED (All 5 domain apps applied to `backend/db.sqlite3`).
- `python manage.py test`: PASSED (8 tests executed and passed in 0.039s).
- `Legacy Database`: 100% UNTOUCHED (Read-only verification confirmed).
