# FarmSync — Application Access & Login Credentials

**Project**: FarmSync — Intelligent Animal Intrusion Detection & Farm Management System  
**Status**: Active & Pre-Configured in Local SQLite Database (`backend/db.sqlite3`)

---

## 1. Application Access URLs

| Interface | URL | Purpose |
| :--- | :--- | :--- |
| **Modern Web Application** | `http://localhost:8080` (or `http://localhost:5173`) | Primary React 19 Single Page Application |
| **REST API Gateway & Docs** | `http://localhost:8000/api/v1/` | Browsable REST API schema & endpoints |
| **Django Administration** | `http://localhost:8000/admin/` | Superuser management console |
| **Launchpad Bridge** | `http://localhost:8000/` | Root launchpad & service status checker |

---

## 2. Default User Accounts & Credentials (Development/Demo)

### Account 1: Administrator / Superuser
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@farmsync.local`
- **Role**: Superuser & Staff (Full Administrative Access)
- **Permissions**: Full CRUD on Farmers, Attendance, Tasks, Project Settings, Detection Thresholds, Camera Index, Email Configuration, Alert Receivers, and Django Admin Portal.

### Account 2: Farm Manager / Staff
- **Username**: `farm_manager`
- **Password**: `manager123`
- **Email**: `manager@farmsync.local`
- **Role**: Staff Member
- **Permissions**: Full operational CRUD on Farmers roster, Daily Attendance Logging (Check-in/Check-out), Task Assignments, and Live Camera & AI Monitoring.

### Account 3: Farm Worker / Field Operator
- **Username**: `farmer_john`
- **Password**: `worker123`
- **Email**: `john@farmsync.local`
- **Role**: Regular Worker (Non-Staff)
- **Permissions**: Read-only access to Workforce Directory and Hazard Alerts audit trail; Submit personal shift check-in / check-out; Run manual snapshot image detection analysis.

---

## 3. How to Create Additional Superusers (CLI)

To create a new superuser account manually via terminal:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the Django `createsuperuser` command:
   ```bash
   python manage.py createsuperuser
   ```

3. Follow the interactive prompts to enter Username, Email, and Password.
