# FarmSync Project Setup & Developer Running Guide

**Project**: FarmSync / Intelligent Animal Detection & Smart Farm Management System  
**Document**: Local Environment Setup, Running Guide & Troubleshooting Manual  
**Architecture**: Decoupled Django REST Framework Backend (Port 8000) + React 19 / Vite SPA Frontend (Port 5173)  
**Version**: 2.0 (Production-Ready Decoupled Stack)  

---

## 1. System Requirements & Prerequisites

Before running the FarmSync platform, verify that your development environment satisfies the following requirements:

- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS 12+
- **Python**: Python 3.11.x or Python 3.12.x (64-bit recommended)
- **Node.js**: Node.js 18.x or 20.x with `npm` (or [Bun](https://bun.sh/))
- **Package Manager**: `pip` (version 23.0+) and `npm` (version 9.0+)
- **Virtual Environment**: Python `venv` or `virtualenv`
- **Video Capture Device**: Built-in webcam or USB camera (Index 0). *Note: If no camera is detected, the system automatically falls back to a simulated test stream without crashing.*
- **YOLOv8 Model**: Pre-packaged `yolov8n.pt` located at repository root.
- **Database**: Pre-configured SQLite (`backend/db.sqlite3`). PostgreSQL compatible for enterprise deployments.

---

## 2. Step-by-Step Installation & Local Execution

FarmSync runs in a decoupled architecture where the **Django REST API Backend** and the **Vite React Frontend** operate concurrently.

### Terminal 1: Backend Setup & Execution

#### Step 1: Open Terminal & Navigate to Project Root
Open PowerShell, Command Prompt, or terminal:
```bash
cd AnimalDetection-main
```

#### Step 2: Create & Activate Virtual Environment
```bash
# Create virtual environment (if not already created)
python -m venv env

# Activate on Windows (PowerShell)
.\env\Scripts\Activate.ps1

# Activate on Windows (CMD)
.\env\Scripts\activate.bat

# Activate on macOS / Linux
source env/bin/activate
```

#### Step 3: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Step 4: Configure Backend Environment Variables (Optional)
```bash
cp .env.example .env
```

#### Step 5: Verify Django System Configuration
```bash
python manage.py check
```
*Expected Output: `System check identified no issues (0 silenced).`*

#### Step 6: Apply Database Migrations
```bash
python manage.py migrate
```

#### Step 7: Create an Administrator User
```bash
python manage.py createsuperuser
```
Follow the interactive prompts to set your superuser username, email, and password.

#### Step 8: Start the Django Backend Server
```bash
python manage.py runserver 0.0.0.0:8000
```
*The backend API is now running at `http://localhost:8000` with the REST API at `http://localhost:8000/api/v1/`.*

---

### Terminal 2: Frontend Setup & Execution

Open a **new terminal window**:

#### Step 1: Navigate to the Frontend Directory
```bash
cd AnimalDetection-main/frontend
```

#### Step 2: Configure Frontend Environment Variables
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL=http://localhost:8000` is set in `.env`.

#### Step 3: Install Frontend Dependencies
```bash
npm install
# or with bun:
bun install
```

#### Step 4: Start the Vite Development Server
```bash
npm run dev
```
*The frontend SPA is now running with Hot Module Replacement at `http://localhost:5173`.*

---

## 3. Accessing the Application & Pre-Configured Logins

| Service / Interface | URL | Pre-Configured Credentials |
|---|---|---|
| 🌿 **Modern FarmSync Web Console** | [http://localhost:5173](http://localhost:5173) | `admin` / `admin123` *(Administrator)*<br>`farm_manager` / `manager123` *(Staff)*<br>`farmer_john` / `worker123` *(Worker)* |
| 🔌 **Django REST API Gateway** | [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/) | Interactive DRF browsable API documentation and testing endpoint. |
| 🛠️ **Django Administration Panel** | [http://localhost:8000/admin/](http://localhost:8000/admin/) | `admin` / `admin123` *(Direct database admin controls)* |
| 🚀 **Single-Server Launchpad Bridge** | [http://localhost:8000/](http://localhost:8000/) | Root Django template view with quick links. |

> [!NOTE]
> All pre-configured accounts are active in the local database and detailed in [users.txt](file:///c:/Users/yuvas/Desktop/AnimalDetection-main/users.txt).

---

## 4. Running Automated Tests & Code Quality Checks

### Backend Automated Test Suite (189 Tests)
From the `backend/` directory with `env` activated:
```bash
python manage.py test
```
*Expected Result:* `Ran 189 tests in ~100s - OK` (100% passing).

To run specific app test suites:
```bash
python manage.py test apps.accounts     # JWT Auth & Blacklist
python manage.py test apps.farmers      # Workforce Directory
python manage.py test apps.attendance   # Check-in/out & Reporting
python manage.py test apps.tasks        # Task assignments & lifecycle
python manage.py test apps.detection    # YOLO inference & stream service
python manage.py test apps.alerts       # Immutable hazard alerts
python manage.py test apps.settings_app # Dynamic project settings
python manage.py test apps.dashboard    # KPI analytics & activity
```

### Frontend Code Quality & Production Build
From the `frontend/` directory:
```bash
npm run lint          # Run ESLint across TypeScript / TSX files
npm run build         # Build production bundle to .output/ / dist/
npm run preview       # Preview production build locally
```

---

## 5. Camera & Computer Vision Troubleshooting

### 1. Camera Device Index
- By default, FarmSync searches for camera index `0`.
- If using an external USB webcam, open **Settings** in the web interface and adjust `Camera Hardware Index` to `1` or `2`, then click **Save Project Settings**.
- Changes take effect immediately without requiring a server restart.

### 2. Headless / Server Environments (No Physical Camera)
- If OpenCV cannot access a physical camera device, `VideoStreamService` automatically streams a synthetic placeholder frame (*"FarmSync Camera Stream Active"*).
- The web interface and all automated test suites will continue running without crashing.

### 3. YOLO Model Weights
- The default model weights file is located at `AnimalDetection-main/yolov8n.pt`.
- If missing, the model loader will log a warning and fallback gracefully during automated tests.

---

## 6. Common Errors & Solutions

| Issue | Cause | Solution |
|---|---|---|
| `No module named 'django'` | Virtual environment not activated. | Run `.\env\Scripts\activate` before executing commands. |
| `CORS Error in Browser` | Origin not allowed in backend settings. | Ensure `CORS_ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:5173`. |
| `HTTP 401 Unauthorized` | Missing or expired JWT token. | Sign in through the web login page to acquire a new token. |
| `HTTP 403 Forbidden` | Non-staff user attempting mutation. | Log in with a staff/superuser account to perform mutations. |
| `Port 8000 already in use` | Another process is binding port 8000. | Run `python manage.py runserver 8080` to use an alternate port. |
| `OpenCV VideoCapture failed` | Camera is in use by another application. | Close other webcam applications (e.g. Zoom/Teams) or rely on the synthetic fallback stream. |
| `npm command not found` | Node.js is not installed or not in PATH. | Install Node.js 18+ or 20+ from [nodejs.org](https://nodejs.org/). |

---

## 7. Documentation Cross-Reference Map

For deep technical specifications, refer to the documentation in `docs/`:

- **System Architecture**: [`docs/architecture/FINAL_SYSTEM_ARCHITECTURE.md`](architecture/FINAL_SYSTEM_ARCHITECTURE.md)
- **Frontend Architecture**: [`docs/architecture/STEP_19_FRONTEND_ARCHITECTURE.md`](architecture/STEP_19_FRONTEND_ARCHITECTURE.md)
- **REST API Endpoint Index**: [`docs/api/FINAL_API_INDEX.md`](api/FINAL_API_INDEX.md)
- **Production Deployment & Security**: [`docs/qa/STEP_18_DEPLOYMENT_READINESS.md`](qa/STEP_18_DEPLOYMENT_READINESS.md)
- **Examiner & Viva Submission Checklist**: [`docs/FINAL_SUBMISSION_CHECKLIST.md`](FINAL_SUBMISSION_CHECKLIST.md)
