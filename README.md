# SecureDataOps

SecureDataOps is a staged portfolio project for a production-oriented secure data platform. Phase 1 establishes a clean full-stack foundation with a React frontend, FastAPI backend, PostgreSQL, SQLAlchemy, Alembic, pytest, Docker, and Docker Compose.

DPDP-oriented privacy controls are intentionally planned for later phases. This Phase 1 application should not be treated as legally DPDP compliant.

## Phase 1 Scope

Phase 1 includes:

- FastAPI backend service
- React dashboard for Phase 1 user management
- PostgreSQL persistence
- SQLAlchemy 2.x typed ORM model for users
- Pydantic 2.x request and response schemas
- Alembic migration for the users table
- Dockerized local development with Docker Compose
- pytest foundation for health and user API behavior

Phase 1 intentionally excludes authentication, authorization, consent management, deletion workflows, audit logging, retention policies, Redis, background workers, cloud deployment, CI/CD, and monitoring.

## Architecture

```text
Client
  |
  v
React Frontend
  |
  v
FastAPI
  |
  v
PostgreSQL
```

Docker Compose runs the frontend, backend, and PostgreSQL database locally. The frontend serves the React app through nginx and proxies API requests to the backend service. The backend reads configuration from environment variables and connects to PostgreSQL through the Compose service name `db`.

## Technology Stack

- Python 3.12
- React
- Vite
- TypeScript
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Pydantic 2.x
- Alembic
- pytest
- Docker and Docker Compose

## Repository Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- main.py
|   |-- alembic/
|   |-- tests/
|   |-- alembic.ini
|   |-- Dockerfile
|   |-- .dockerignore
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- services/
|   |   |-- utils/
|   |   `-- App.tsx
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- package.json
|   `-- vite.config.ts
|-- docker-compose.yml
|-- .env.example
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Local Prerequisites

- Docker Desktop or Docker Engine with Compose
- Node.js and npm, if running the frontend outside Docker
- Python 3.12, if running tests outside Docker

## Environment Setup

Create a local `.env` from the example when needed:

```bash
cp .env.example .env
```

The default Docker Compose configuration uses:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/securedataops
APP_ENV=development
BACKEND_CORS_ORIGINS=http://localhost:5173
VITE_API_BASE_URL=
```

Do not commit real `.env` files or credentials.

## Run With Docker Compose

Build and start the local stack:

```bash
docker compose up -d --build
```

The frontend is available at:

```text
http://localhost:5173
```

The backend API remains available at:

```text
http://localhost:8000
```

Run the database migration:

```bash
docker compose exec backend alembic upgrade head
```

Open the API health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

The React frontend can create, list, inspect, edit, and delete Phase 1 user records through the existing FastAPI REST API.

## Run Frontend Locally

From the frontend directory:

```bash
npm install
npm run dev
```

If `VITE_API_BASE_URL` is empty, the frontend uses same-origin API requests. In Docker, nginx proxies those requests to the backend. For a standalone local frontend pointed at the published backend port, set:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Build the frontend:

```bash
npm run build
```

## Run Tests

From the backend directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

Tests currently cover the health endpoint, user request validation, and basic user API behavior using a lightweight service mock. Full PostgreSQL integration tests are intentionally deferred to keep Phase 1 focused and approachable.

## Alembic Migrations

Run migrations inside the backend container:

```bash
docker compose exec backend alembic upgrade head
```

Create a new migration after model changes:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe change"
```

Schema changes should be represented through Alembic migrations instead of manual table creation.

## API Endpoints

- `GET /health`
- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

## Example API Requests

Create a user:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","phone":"+15551234567"}'
```

List users:

```bash
curl http://localhost:8000/api/v1/users
```

Update a user:

```bash
curl -X PUT http://localhost:8000/api/v1/users/<user_id> \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Byron"}'
```

Delete a user:

```bash
curl -X DELETE http://localhost:8000/api/v1/users/<user_id>
```

## Current Limitations

- No authentication or authorization
- No consent management
- No DPDP workflow implementation
- No audit logging or retention automation
- No Redis, background workers, or cloud deployment
- No monitoring or CI/CD pipeline
- User API tests use a lightweight mocked persistence layer; database-backed integration tests can be added in a later hardening phase

## Planned Future Phases

Later phases can add authentication, consent management, deletion workflows, audit logging, retention policies, Redis-backed workers, AWS deployment, DevSecOps CI/CD, monitoring, and SRE practices.
