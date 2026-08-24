# FarmSync Django REST API Backend

**Project**: FarmSync / Intelligent Animal Detection System  
**Layer**: Backend REST API & Services Layer  
**Framework**: Django 5.x & Django REST Framework  
**Status**: FOUNDATION INITIALIZED (Step 1)  

---

## 1. Directory Structure

```text
backend/
├── config/             # Django Project Configuration & URL Gateway
│   ├── settings.py     # Main Settings (DRF, CORS, Database, Media)
│   ├── urls.py         # Global Routing Router
│   ├── wsgi.py         # WSGI Entry Point
│   └── asgi.py         # ASGI Entry Point
│
├── apps/               # Modular Domain Business Applications
│   └── README.md       # App Initialization Plan (Option B)
│
├── services/           # Non-Web Background Engine Subsystems
│   ├── yolo/           # YOLOv8 Detection & Inference Subsystem
│   ├── camera/         # Camera Hardware & MJPEG Stream Subsystem
│   └── notifications/  # Non-blocking SMTP & Buzzer Subsystem
│
├── media/              # Managed Media Storage (Snapshots, Audio)
│   └── .gitkeep
│
├── manage.py           # Django Management CLI
├── requirements.txt    # Foundation Dependencies
├── .env.example        # Environment Variables Template
└── README.md           # Backend Documentation
```

---

## 2. Setup & Verification

### Step 1: Configure Environment Variables
Copy `.env.example` to create your local `.env`:
```bash
cp .env.example .env
```

### Step 2: Install Foundation Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify Django System Configuration
Run the Django system check:
```bash
python manage.py check
```

---

## 3. Architecture Rules
1. **API-First**: All backend views return JSON payloads. No Django HTML templates or direct Jinja rendering.
2. **Decoupled Frontend**: All external clients (SPAs, mobile apps, Lovable AI frontends) authenticate via JWT and interact through `/api/...`.
3. **Write-Only Secrets**: Sensitive credentials (e.g. SMTP passwords) are never returned across the wire.
