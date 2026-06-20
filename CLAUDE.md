# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPlane — 轻量级团队项目协作与缺陷跟踪系统。软件体系结构课程项目，基于 Plane 的简化实现。

**Key constraint:** All API responses are wrapped by `APIRenderer` into `{success, data, message}` format. The frontend axios interceptor (in `frontend/src/lib/api.ts`) unwraps `response.data = response.data.data`, so after the interceptor, the data is the raw payload (array, object, etc.) — **NOT** inside a `results` wrapper.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (React 19) + TypeScript 5 + TailwindCSS 4 |
| Backend | Django 5 + DRF + Daphne (ASGI) |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 + Celery |
| File Storage | MinIO (S3-compatible) |
| Realtime | Django Channels + WebSocket |
| PM | uv (Python) / pnpm (Node) |

## Architecture

### Backend (`backend/`)

11 Django apps under `backend/apps/`:

- `core` — Base classes, permissions, pagination, APIRenderer, custom exceptions
- `accounts` — User registration, login, JWT, profile
- `workspaces` — Workspace CRUD, members
- `projects` — Project CRUD, members, WebSocket consumer
- `tasks` — Task CRUD, kanban/list views, status management, drag-drop
- `iterations` — Sprint/iteration management
- `modules` — Feature module categorization
- `comments` — Task comments
- `attachments` — File upload via MinIO
- `notifications` — Real-time notification system (WebSocket + REST)
- `activities` — Operation audit log
- `statistics` — Project/iteration analytics

**Key URL patterns** (`backend/config/urls.py`):
- `/api/auth/` — Registration, login, logout, password change
- `/api/workspaces/` — Workspace CRUD (nested: `/workspaces/{id}/projects/`)
- `/api/projects/{proj_id}/tasks/` — Task listing/creation
- `/api/projects/{proj_id}/task-statuses/` — Kanban column management
- `/api/projects/{proj_id}/iterations/` — Iteration management
- `/api/projects/{proj_id}/modules/` — Module management
- `/api/projects/{pk}/statistics/` — Project stats
- `/api/tasks/` — Task detail/edit/delete
- `/api/tasks/{task_id}/comments/` — Task comments
- `/api/tasks/{task_id}/attachments/` — Task attachments
- `/api/notifications/` — User notifications
- `/ws/projects/{project_id}/` — WebSocket for real-time collaboration
- `/api/docs/` — Swagger UI (drf-spectacular)

**Pagination:** `StandardPagination` in `core/pagination.py` — page/page_size based. The APIRenderer extracts `results` from paginated responses and wraps pagination metadata separately.

**Default task statuses** (auto-created on project creation): Backlog → 待办 → 进行中 → 待评审 → 已完成 → 已取消

### Frontend (`frontend/`)

Next.js 16 App Router with `(authenticated)` route group.

**Key routes:**
- `/` — Landing page
- `/login`, `/register` — Auth pages
- `/dashboard` — Workspace list
- `/workspaces/[wsId]` — Project list within workspace
- `/projects/[projId]` — Kanban board (default project view)
- `/projects/[projId]/list` — List view
- `/projects/[projId]/iterations` — Iteration management
- `/projects/[projId]/modules` — Module management
- `/projects/[projId]/settings` — Project settings + stats
- `/tasks/[taskId]` — Task detail (comments, attachments, activity log)
- `/settings` — User profile settings

**State management:** Zustand stores (`frontend/src/stores/`) for auth, app, and notifications.

**API client:** Axios instance in `frontend/src/lib/api.ts` with JWT interceptor (auto-refresh on 401) and APIRenderer response unwrapping.

**Important:** `NEXT_PUBLIC_*` env vars are build-time in Next.js. For Docker deployment, they must be passed as build `args`, not runtime `environment`.

### Infrastructure

- **Docker Compose** (`docker-compose.yml` at root) — Full stack deployment
- **Nginx** (`nginx/nginx.conf`) — Reverse proxy, routes `/api/`, `/ws/`, `/admin/` to backend, rest to frontend
- **Port overrides** via `.env`: `NGINX_PORT`, `DB_PORT`, `REDIS_PORT`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`

## Common Commands

### Docker (production deployment)

```bash
# Start everything
docker compose up -d

# Rebuild and restart a specific service (after code changes)
docker compose up -d --build frontend
docker compose up -d --build backend

# View logs
docker compose logs frontend --tail 30
docker compose logs backend --tail 30
docker compose logs nginx --tail 20

# Migrate database
docker compose exec backend uv run python manage.py migrate

# Seed demo data (3 teams, ~65 tasks)
docker compose exec backend uv run python manage.py seed_data

# Clear and re-seed
docker compose exec backend uv run python manage.py seed_data --clear

# Create superuser
docker compose exec backend uv run python manage.py createsuperuser

# Run management commands
docker compose exec backend uv run python manage.py <command>

# Shell access
docker compose exec backend bash
```

### Local Development

```bash
# Backend (from backend/)
uv sync
uv run python manage.py migrate
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Frontend (from frontend/)
pnpm install
pnpm dev                    # Starts on port 5173
```

### Testing

```bash
# Run all backend tests (from backend/ or via Docker)
uv run pytest                          # Local
docker compose exec backend uv run pytest  # Docker

# Run with coverage
uv run pytest --cov=apps --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_auth.py
uv run pytest apps/tasks/tests/

# Run a single test
uv run pytest tests/test_auth.py::TestUserRegistration::test_register_success -v

# Run performance tests
uv run pytest tests/test_performance.py -v

# Run fault injection tests
uv run pytest tests/test_fault_injection.py -v

# Frontend checks
pnpm lint                    # ESLint
npx tsc --noEmit             # TypeScript check (from frontend/)
```

## Important Gotchas

1. **API data format:** The `APIRenderer` wraps all responses. The axios interceptor in `frontend/src/lib/api.ts` unwraps `response.data = body.data`. For paginated endpoints, the array is directly in `data` (not `data.results`). Use `Array.isArray(data) ? data : data.results || []` pattern when consuming API lists.

2. **NEXT_PUBLIC_* building:** These variables are baked into JS at build time. For Docker: pass via `build.args` in docker-compose.yml, not `environment`.

3. **Nginx DNS cache:** When containers are recreated, Docker reassigns IPs. Always run `docker compose restart nginx` after rebuilding upstream services, or nginx will return 502 errors.

4. **WebSocket:** Requires Daphne (ASGI), not Django's `runserver`. The backend CMD uses `uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application`.

5. **Task creation requires status:** The `TaskCreateSerializer` auto-assigns the first "unstarted" status if none is provided. The kanban view filters by `t.status === col.id` (string UUID comparison).
