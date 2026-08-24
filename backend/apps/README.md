# Backend Applications Directory (`backend/apps/`)

**Layer**: Django Modular Domain Applications  
**Strategy**: Option B (Step-by-Step App Initialization)  
**Status**: DIRECTORY FOUNDATION CREATED  

---

## Architectural Rationale: Option B

Rather than generating empty stub applications with fake placeholder files that could trigger circular imports or break Django system checks, **Option B** establishes the clean architectural boundary for domain applications first. 

Each domain app will be initialized systematically with its dedicated models, serializers, views, permissions, and test suites during its designated migration step:

| Target Domain App | Scope & Responsibility | Scheduled Step |
| :--- | :--- | :--- |
| `apps.core` | Base abstract models, common pagination, global API exception handlers | Step 2 / Step 3 |
| `apps.accounts` | User authentication, JWT handlers, profile management, RBAC | Step 4 |
| `apps.settings_app` | Dynamic database-backed system settings, email configs, threat rules | Step 5 |
| `apps.dashboard` | Top-level analytics, aggregate counters, system status endpoints | Step 6 |
| `apps.farmers` | Farmer workforce management (CRUD, field assignments) | Step 7 |
| `apps.tasks` | Task delegation, assignment board, worker status tracking | Step 8 |
| `apps.attendance` | Geolocation check-in/out, hours computation, date-filtered reports | Step 9 |
| `apps.detection` | Detection logs, image queries, camera streaming API controller | Step 11 / Step 12 |
| `apps.alerts` | Alert event history, notification logs, delivery verification | Step 13 |

---

## Guidelines for Apps
- **Strict Isolation**: Apps communicate with each other through standard Django ORM relations or dedicated service layers.
- **RESTful ViewSets**: All views inherit from `rest_framework.views.APIView` or `rest_framework.viewsets.ModelViewSet`.
- **Zero Template Coupling**: No app contains HTML templates or calls `render()`.
