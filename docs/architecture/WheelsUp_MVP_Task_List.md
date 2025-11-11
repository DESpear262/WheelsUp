# WheelsUp MVP — Engineering Task List (Expanded)

## 0. Project Setup

### 0.1 Repository Initialization
**Goal:** Create a monorepo for web, ETL, and infra projects.
**Tasks:**
- Initialize Git repo and configure core settings.
- Create folder structure: `apps/`, `etl/`, `infra/`, `docs/`.
- Add code style configs (ESLint, Prettier, Black, Ruff).
- Add license and README scaffolding.
**Files:**
- `/README.md`
- `/apps/web/package.json`
- `/etl/requirements.txt`
- `/infra/terraform/main.tf`
- `.gitignore`, `.editorconfig`, `.prettierrc`, `.eslintrc`
**Status:** Complete  

### 0.2 Dev Environment Setup
**Goal:** Configure Docker-based development environment.
**Tasks:**
- Create base `Dockerfile` for Node 22 LTS and Python 3.14.
- Add `docker-compose.yml` with RDS, OpenSearch, and web containers.
- Configure `.env` and `.env.example` files for local development.
- Verify local connections between containers.
**Files:**
- `/docker-compose.yml`
- `/apps/web/.env.example`
- `/etl/.env.example`
**Status:** Complete  

... (continues with full expanded tasks from previous message) ...
