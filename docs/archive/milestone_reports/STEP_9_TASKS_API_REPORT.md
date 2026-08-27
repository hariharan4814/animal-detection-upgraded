# STEP 9: Tasks Management REST API Migration Report

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 9 – Tasks Management REST APIs  
**Date**: August 24, 2026  
**Status**: COMPLETE & FULLY VERIFIED  

---

## 1. Executive Summary

Step 9 of the FarmSync backend migration is complete. The legacy Flask/SQLite task delegation system has been migrated into a decoupled, secure, and fully-tested Django REST API under `apps.tasks`.

### Core Highlights:
- **Zero Schema Migrations**: The existing `Task` model created in Step 3 (`backend/apps/tasks/models.py`) was reused with 100% fidelity. No duplicate models or new migrations were created.
- **Legacy Safety**: Legacy SQLite database (`data.db`) was inspected strictly in READ-ONLY mode (`file:../data.db?mode=ro`) and was not modified. Legacy Python modules (`modules/tasks.py`, `app.py`, `templates/tasks.html`) remain completely untouched.
- **Role-Based Security**: Secured with `IsAdminOrReadOnly`. Regular authenticated workers have read-only access to view task assignments, while mutations (create, full update, partial status update, delete) are strictly limited to staff and farm administrators.
- **Comprehensive Test Suite**: Added 37 comprehensive unit, permission, validation, relational, and integration test cases in `apps.tasks.tests`. Total test suite passes with **121 / 121 tests passing** (up from 84 baseline tests).

---

## 2. Legacy Evidence Audit & Classification Matrix

Before implementing the API layer, a rigorous evidence audit was performed across legacy source code (`modules/tasks.py`, `app.py`, `templates/tasks.html`, `database/db.py`) and legacy `data.db` (read-only mode).

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

## 3. Actual Model Reused

The existing model at `backend/apps/tasks/models.py` was reused directly:

```python
class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    task_name = models.CharField(max_length=255, help_text="Description of the assigned farm task")
    assigned_to = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks',
        help_text="Farmer assigned to this task"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Task completion status"
    )
    date = models.DateField(default=timezone.now, help_text="Date when the task was assigned")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
```

---

## 4. REST API Endpoints Reference

Base path: `/api/v1/tasks/`

| HTTP Method | URL Path | Permission | Description | Classification |
|---|---|---|---|---|
| `GET` | `/api/v1/tasks/` | Authenticated | List all tasks with optional filters (`status`, `assigned_to`/`farmer_id`, `date`, `start_date`, `end_date`) | **LEGACY-VERIFIED & ENHANCED** |
| `POST` | `/api/v1/tasks/` | Staff / Admin | Create a new task assignment | **LEGACY-VERIFIED** |
| `GET` | `/api/v1/tasks/{id}/` | Authenticated | Retrieve details of a specific task | **DJANGO/API ENHANCEMENT** |
| `PUT` | `/api/v1/tasks/{id}/` | Staff / Admin | Full update of task attributes | **DJANGO/API ENHANCEMENT** |
| `PATCH` | `/api/v1/tasks/{id}/` | Staff / Admin | Partial update / status workflow transitions | **LEGACY-VERIFIED (Status) / ENHANCEMENT** |
| `DELETE` | `/api/v1/tasks/{id}/` | Staff / Admin | Remove a task record | **DJANGO/API ENHANCEMENT** |

---

## 5. Security & Authorization Architecture

- **Unauthenticated Access**: All endpoints reject unauthenticated requests with `HTTP 401 Unauthorized`.
- **Regular Authenticated Users**: Have read-only access (`GET` list and detail). Attempts to perform write actions (`POST`, `PUT`, `PATCH`, `DELETE`) return `HTTP 403 Forbidden`.
- **Staff / Admin Users**: Authorized for all operations (read, create, full update, partial update, delete).
- **CSRF & CORS**: Session-authenticated requests use CSRF protection; JWT bearer token requests bypass CSRF per DRF standard. CORS allows frontend integrations.

---

## 6. Input Validation & Serializer Logic

`TaskSerializer` in `backend/apps/tasks/serializers.py` implements:
- **`task_name`**: Stripped and validated; blank and whitespace-only strings are rejected with `HTTP 400 Bad Request`.
- **`assigned_to`**: Foreign key to `Farmer`. Nonexistent worker IDs are rejected with `HTTP 400 Bad Request`. Unassigned / null worker assignments are permitted.
- **`assigned_to_name`**: Read-only serialized property returning the worker's full name (`source='assigned_to.name'`, default `None`).
- **`status`**: Validated against verified choices (`['Pending', 'Completed']`). Invalid choices rejected with `HTTP 400 Bad Request`.
- **`date`**: Handled seamlessly; defaults to current date (`timezone.localdate()`) if omitted on creation.
- **Read-Only Fields**: `id`, `assigned_to_name`, `created_at`, and `updated_at` are protected against client tampering.

---

## 7. Automated Test Suite Results

The task test suite in `backend/apps/tasks/tests.py` was expanded to 38 test cases covering all lifecycle paths:

1. **Authentication Tests**:
   - `test_01_unauthenticated_list_rejected` (401)
   - `test_02_unauthenticated_detail_rejected` (401)
   - `test_03_unauthenticated_create_rejected` (401)
   - `test_04_unauthenticated_put_rejected` (401)
   - `test_05_unauthenticated_patch_rejected` (401)
   - `test_06_unauthenticated_delete_rejected` (401)

2. **Read Access Tests**:
   - `test_07_authenticated_regular_user_can_list_tasks` (200)
   - `test_08_empty_task_list_returns_empty_array` (200)
   - `test_09_authenticated_regular_user_can_retrieve_detail` (200)
   - `test_10_nonexistent_task_returns_404` (404 envelope)

3. **Write Permission Tests**:
   - `test_11_regular_user_cannot_create_task` (403)
   - `test_12_regular_user_cannot_put_task` (403)
   - `test_13_regular_user_cannot_patch_task` (403)
   - `test_14_regular_user_cannot_delete_task` (403)
   - `test_15_staff_can_create_task` (201)

4. **Validation Tests**:
   - `test_16_blank_task_name_rejected` (400)
   - `test_17_whitespace_only_task_name_rejected` (400)
   - `test_18_invalid_assigned_farmer_rejected` (400)
   - `test_19_unassigned_task_creation_succeeds` (201)
   - `test_20_invalid_status_rejected` (400)
   - `test_21_valid_verified_statuses_accepted` (201)
   - `test_22_default_status_is_pending` (201)

5. **CRUD & Update Behavior**:
   - `test_23_staff_can_put_full_update` (200)
   - `test_24_staff_can_patch_and_preserves_unspecified_fields` (200)
   - `test_25_status_transition_workflow` (200)
   - `test_26_staff_can_delete_task` (200)

6. **Relationships & Cascades**:
   - `test_27_assigned_farmer_serialization`
   - `test_28_farmer_deletion_sets_task_assigned_to_null` (`on_delete=models.SET_NULL`)

7. **Filtering & Ordering**:
   - `test_29_filter_by_status` (`Pending`, `Completed`)
   - `test_30_filter_by_assigned_to_and_farmer_id`
   - `test_31_filter_by_exact_date`
   - `test_32_filter_by_date_range` (`start_date`, `end_date`)
   - `test_33_invalid_filter_values_handled_gracefully`
   - `test_34_combined_multi_filtering`
   - `test_35_response_format_envelope`
   - `test_36_tasks_ordering_reverse_id`

8. **Model Unit Tests**:
   - `test_create_task`
   - `test_unassigned_task_str_representation`

---

## 8. Final Verification Output

All verification commands executed from `C:\Users\yuvas\Desktop\AnimalDetection-main\backend`:

### A. `python manage.py check`
```
System check identified no issues (0 silenced).
```
**Result**: PASS

### B. `python manage.py makemigrations --check`
```
No changes detected
```
**Result**: PASS

### C. `python manage.py test apps.tasks`
```
Creating test database for alias 'default'...
......................................
----------------------------------------------------------------------
Ran 38 tests in 22.161s

OK
Destroying test database for alias 'default'...
Found 38 test(s).
System check identified no issues (0 silenced).
```
**Result**: PASS (38 / 38 passed)

### D. `python manage.py test` (Full Project Suite)
```
Creating test database for alias 'default'...
.........................................................................................................................
----------------------------------------------------------------------
Ran 121 tests in 67.155s

OK
Destroying test database for alias 'default'...
Found 121 test(s).
System check identified no issues (0 silenced).
```
**Result**: PASS (121 / 121 passed)

### E. `python manage.py check --deploy`
```
System check identified some issues:

WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. If your entire site is served only over SSL, you may want to consider setting a value and enabling HTTP Strict Transport Security. Be sure to read the documentation first; enabling HSTS carelessly can cause serious, irreversible problems.
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. Unless your site should be available over both SSL and non-SSL connections, you may want to either set this setting True or configure a load balancer or reverse-proxy server to redirect all connections to HTTPS.
?: (security.W009) Your SECRET_KEY has less than 50 characters, less than 5 unique characters, or it's prefixed with 'django-insecure-' indicating that it was generated automatically by Django. Please generate a long and random value, otherwise many of Django's security-critical features will be vulnerable to attack.
?: (security.W012) SESSION_COOKIE_SECURE is not set to True. Using a secure-only session cookie makes it more difficult for network traffic sniffers to hijack user sessions.
?: (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' in your MIDDLEWARE, but you have not set CSRF_COOKIE_SECURE to True. Using a secure-only CSRF cookie makes it more difficult for network traffic sniffers to steal the CSRF token.
?: (security.W018) You should not have DEBUG set to True in deployment.

System check identified 6 issues (0 silenced).
```
**Result**: Expected development-mode warnings present due to local `DEBUG=True` setting.

### F. `git status`
```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   apps/tasks/tests.py
	modified:   config/urls.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	apps/tasks/serializers.py
	apps/tasks/urls.py
	apps/tasks/views.py
```
**Result**: Clean working tree restricted exclusively to Step 9 task files.

---

## 9. Legacy Safety Verification

- **Legacy Database (`data.db`)**: Opened strictly in read-only mode (`file:data.db?mode=ro`). Zero writes, updates, deletes, schema alters, or migrations were executed against `data.db`.
- **Legacy Source Files**: `modules/tasks.py`, `app.py`, and `templates/tasks.html` were not modified.
- **Git Commit Safety**: No `git add`, `git commit`, or `git push` commands were executed.
