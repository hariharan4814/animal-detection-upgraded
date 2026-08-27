# FarmSync — Modern Web Application Frontend

**Architecture**: Decoupled Single-Page Application (SPA)  
**Framework**: React 19 + TypeScript + Vite 8 + TanStack Router + TanStack Query v5 + Tailwind CSS v4 + Radix UI  
**Target Backend**: Django REST Framework API Gateway (`http://localhost:8000/api/v1/`)

---

## 1. Overview & Architectural Role

This repository contains the presentation layer of the **FarmSync Intelligent Animal Detection & Farm Management System**. The frontend operates as a completely decoupled client communicating with the Django REST Framework backend over authenticated REST APIs (JSON) and an authenticated multipart MJPEG live video stream.

All business logic, authentication token lifecycles, YOLO inference, detection snapshot persistence, and hazard alert creation are authoritatively executed and governed by the Django backend.

---

## 2. Technology Stack

- **Core**: React 19, TypeScript (Strict Mode), Vite 8
- **Routing**: `@tanstack/react-router` (File-based routing under `src/routes/`)
- **Server State & Data Fetching**: `@tanstack/react-query` v5
- **UI Components & Primitives**: Radix UI primitives (`@radix-ui/*`), Shadcn-compatible design patterns
- **Styling**: Tailwind CSS v4 (`@tailwindcss/vite`), `tw-animate-css`, `clsx`, `tailwind-merge`
- **Icons & Notifications**: `lucide-react`, `sonner` toast notifications
- **Forms & Validation**: `react-hook-form`, `@hookform/resolvers`, `zod`
- **Charts & Visualization**: `recharts`

---

## 3. Quick Start & Local Development

### Prerequisites

- Node.js 18.x or 20.x ([Download Node.js](https://nodejs.org/)) (or [Bun](https://bun.sh/))
- Active FarmSync Django Backend running on `http://localhost:8000`

### Step 1: Install Dependencies

```bash
cd frontend
npm install
# or with bun:
bun install
```

### Step 2: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Default configuration:

```env
# Base origin of the Django backend (no trailing /api/v1)
VITE_API_BASE_URL=http://localhost:8000
```

### Step 3: Start the Development Server

```bash
npm run dev
# or with bun:
bun dev
```

Open [http://localhost:8080](http://localhost:8080) (or [http://localhost:5173](http://localhost:5173)) in your browser.

---

## 4. Available NPM Scripts

| Script            | Command        | Purpose                                                                                  |
| ----------------- | -------------- | ---------------------------------------------------------------------------------------- |
| `npm run dev`     | `vite dev`     | Starts local Vite dev server with Hot Module Replacement (HMR) (default port 8080/5173). |
| `npm run build`   | `vite build`   | Compiles TypeScript and builds optimized production bundle to `.output/` / `dist/`.      |
| `npm run preview` | `vite preview` | Previews the production build locally.                                                   |

| `npm run lint` | `eslint .` | Runs ESLint analysis across all TypeScript & JSX sources. |
| `npm run format` | `prettier --write .` | Auto-formats code with Prettier. |

---

## 5. Application Views & Routing Hierarchy

The application structure is organized in `src/routes/`:

```
src/routes/
├── __root.tsx          # Root application shell, React Query provider, Auth provider, Sonner toast
├── login.tsx           # Authentication screen (JWT username/password submission)
├── app.tsx             # Authenticated layout wrapper with responsive navigation sidebar
├── app.index.tsx       # Main Dashboard (Real-time KPI metrics, active animal alerts, activity feed)
├── app.farmers.tsx     # Farmers Directory (Workforce roster, phone, sector CRUD)
├── app.attendance.tsx  # Smart Attendance (Check-in with GPS, Check-out, shift hours report)
├── app.tasks.tsx       # Task Management (Agricultural task creation, status toggle: Pending ↔ Completed)
├── app.monitoring.tsx  # Live AI Camera Feed (MJPEG stream player + YOLO manual image analysis)
├── app.detection-logs.tsx # Detection History (Intrusion logs, confidence scores, snapshot drawer)
├── app.alerts.tsx      # Hazard Alerts (Immutable audit trail of automated email & buzzer dispatches)
└── app.settings.tsx    # System Configuration (Detection threshold, camera index, hourly wage, SMTP config)
```

---

## 6. API Client & Authentication Layer

### Centralized API Client (`src/lib/api.ts`)

All network interactions route exclusively through `apiRequest<T>()`:

1. **Automatic Bearer Header Injection**: Attaches `Authorization: Bearer <access_token>` from `localStorage`.
2. **Silent JWT Refresh on 401**: When an access token expires, interceptor transparently calls `POST /api/v1/auth/refresh/` using the stored refresh token, updates storage, and retries the original request.
3. **Graceful Session Invalidation**: If the refresh token is also expired or invalid, clears stored credentials and redirects to `/login`.
4. **Structured Error Handling**: DRF error responses are parsed into `ApiError` instances with access to field-level errors (`error.fieldErrors`).

### Authenticated MJPEG Live Stream

The live camera stream player in `src/routes/app.monitoring.tsx` loads:

```
${VITE_API_BASE_URL}/api/v1/detection/stream/?token=${accessToken}
```

The token is safely passed via query parameters to allow native `<img>` tag MJPEG streaming while maintaining strict JWT verification.

### Role-Based Access Control (RBAC) UI Gating

- Staff/Admin permissions (`is_staff: true`) grant access to create, update, or delete farmers, tasks, attendance records, and project settings.
- Regular farm workers (`is_staff: false`) have write controls automatically hidden in the UI while retaining access to submit their own attendance and view monitoring feeds.

---

## 7. Directory Structure

```
frontend/
├── src/
│   ├── components/       # UI Components
│   │   ├── common/       # Loading spinners, empty states, error fallbacks, page headers
│   │   ├── dashboard/    # KPI statistic cards, status badges
│   │   ├── layout/       # App layout, responsive sidebar, top navbar
│   │   └── ui/           # Radix UI primitives (Button, Dialog, Sheet, Select, Tabs, etc.)
│   ├── hooks/            # TanStack Query custom hooks (src/hooks/use-api.ts)
│   ├── lib/              # Core utilities
│   │   ├── api.ts        # Centralized DRF API Client
│   │   ├── auth.tsx      # Authentication Context & Session Provider
│   │   ├── format.ts     # Date, currency, and confidence score formatters
│   │   └── utils.ts      # Class merging utilities
│   ├── routes/           # TanStack file-based routes
│   └── types/
│       └── api.ts        # TypeScript interfaces matching DRF response envelopes
├── public/               # Favicon and static assets
├── index.html            # Single-page application HTML entrypoint
├── package.json          # Node dependencies and scripts
├── tsconfig.json         # Strict TypeScript configuration
└── vite.config.ts        # Vite configuration with React & Tailwind plugins
```
