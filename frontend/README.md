# FarmSync Frontend Application

**Project**: FarmSync / Intelligent Animal Detection System  
**Layer**: Independent Frontend Presentation Layer  
**Status**: FOUNDATION INITIALIZED (Decoupled SPA / Lovable AI Ready)  

---

## 1. Architectural Principles

The FarmSync frontend is engineered as an **independently deployable and replaceable Single-Page Application (SPA)** that interacts with the backend strictly through documented REST APIs.

### Key Rules
1. **Total Independence from Django**:
   - The frontend contains zero Python code and zero server-side Jinja/Django template rendering.
   - It is hosted and bundled independently (e.g. via Vite/Node/Vercel/Static hosting).
2. **API-First Communication**:
   - All dynamic data, stats, workforce records, attendance logs, tasks, and alerts are fetched via HTTP REST API endpoints documented in `docs/api/api_contract.md`.
   - Live video feeds are consumed directly via the dedicated MJPEG streaming endpoint:
     ```html
     <img src="http://localhost:8000/api/detection/camera/stream/" alt="Live Stream" />
     ```
3. **No Direct Database Access**:
   - The frontend has zero direct connection to SQLite, PostgreSQL, or any storage medium. All data operations are validated and executed by the Django backend.
4. **No Critical Authorization Logic**:
   - The backend enforces all permissions, role checks, and JWT validations. The frontend only adjusts UI visibility based on the decoded token claims for user convenience.
5. **Future Lovable AI Replacement Readiness**:
   - Because the backend exposes a complete, self-describing REST API with CORS support and OpenAPI 3.0 documentation, this entire frontend can be replaced or regenerated using Lovable AI or any SPA framework (React, Vue, Svelte) without changing a single line of backend Python code.
6. **Design System Preservation**:
   - The frontend retains the light-mode green glassmorphism design system (`static/style.css` in legacy), which provides a modern visual aesthetic across all screens.

---

## 2. API Contract Reference

For the comprehensive specification of endpoints, payload structures, authentication headers, and error formats, see:
- [API Contract Specification](../docs/api/api_contract.md)

---

## 3. Current Migration Stage

- **Current Status**: Foundation created. 
- **Next Steps**: In Step 15–16, modern decoupled frontend components consuming the Django REST API will be integrated and verified.
