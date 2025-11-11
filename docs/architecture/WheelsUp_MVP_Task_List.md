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
**Status:** Complete - QC Passed
**QC Notes:**
- Repository structure is properly initialized
- Git repository configured
- Basic folder structure in place
- Dependencies partially installed (Python 3.14 compatibility issues noted)
- Docker setup validated with warnings about missing environment variables

**Coding Standards Check:** ✅ PASSED
- Function lengths within limits
- File sizes acceptable for current codebase

**Test Coverage:** ⚠️ LIMITED
- Basic test harness implemented but dependency issues prevent full execution
- Python 3.14 compatibility issues with some packages
- Core functionality (imports, basic operations) verified manually  

### 0.2 Dev Environment Setup
**Goal:** Configure Docker-based development environment.
**Tasks:**
- Create base `Dockerfile` for Node 22 LTS and Python 3.14.
- Add `docker-compose.yml` with RDS, NewSearch, and web containers.
- Configure `.env` and `.env.example` files for local development.
- Verify local connections between containers.
**Files:**
- `/docker-compose.yml`
- `/apps/web/.env.example`
- `/etl/.env.example`
**Status:** Complete - QC Passed with Notes
**QC Notes:**
- Docker Compose configuration is syntactically valid
- Dockerfiles are properly structured
- Health checks and networking configured
- ⚠️ Warnings: Missing environment variables (expected for local setup)
- ⚠️ Obsolete 'version' field in docker-compose files (minor issue)

**Configuration Validation:** ✅ PASSED
- docker-compose config validates successfully
- Service definitions are correct
- Port mappings and volumes configured properly  

## 1. Data Engineering & ETL

### 1.1 Source Discovery & Crawl Seeding
**Goal:** Identify and configure crawl seed sources.
**Tasks:**
- Research top flight school directories and FAA datasets.
- Implement a seed script to produce a unique list of school URLs.
- Store canonical identifiers (domain, phone, ICAO).
- Log discovery stats and duplicates.
**Files:**
- `/etl/pipelines/discover/seed_sources.py`
- `/etl/configs/sources.yaml`
**Status:** Complete  

### 1.2 Crawling Pipeline
**Goal:** Scrape raw HTML/PDF data for known schools.
**Tasks:**
- Implement Scrapy spiders for each seed source.
- Add Playwright handler for JS-heavy or Cloudflare-protected sites.
- Handle retries, timeouts, and error logging.
- Upload results to S3 in `raw/{snapshot_id}/{source}/`.
**Files:**
- `/etl/pipelines/crawl/spider.py`
- `/etl/pipelines/crawl/playwright_spider.py`
- `/etl/utils/s3_upload.py`
- `/etl/configs/crawl_settings.yaml`
**Status:** Complete  

### 1.3 Text Extraction
**Goal:** Convert raw HTML/PDFs into normalized text.  
**Tasks:**  
- Build HTML cleaner (strip scripts, headers, footers).  
- Implement PDF text extraction + optional OCR fallback.  
- Save output JSON with text and metadata per document.  
- Add basic text length and quality checks.  
**Files:**  
- `/etl/pipelines/extract/html_to_text.py`  
- `/etl/pipelines/extract/pdf_to_text.py`  
- `/etl/pipelines/extract/__init__.py`  
- `/etl/utils/text_cleaning.py`
**Status:** Complete  

### 1.4 LLM Extraction
**Goal:** Extract structured schema fields via Claude or GPT.
**Tasks:**
- Write structured prompt templates for school data fields.
- Implement batch processor with caching and token counting.
- Parse JSON outputs and validate against Pydantic schema.
- Record extraction confidence and source provenance.
**Files:**
- `/etl/pipelines/llm/extract_school_data.py`
- `/etl/pipelines/llm/prompts/school_prompt.txt`
- `/etl/schemas/school_schema.py`
- `/etl/utils/llm_client.py`
**Status:** Complete (Agent: White)
**Completion Notes:**
- Created LLM client with Claude 3.5 Sonnet (Bedrock) primary + GPT-4o fallback
- Built comprehensive prompt template for structured flight school data extraction
- Implemented batch processing pipeline with caching, error handling, and token tracking
- Added Pydantic schema validation and confidence scoring
- Included provenance tracking and metadata collection
- Pipeline ready for processing extracted text files from ETL pipeline

### 1.5 Validation & Normalization
**Goal:** Enforce data consistency and normalize units.  
**Tasks:**  
- Validate cost, duration, and fleet fields.  
- Convert rates (USD/hr → total cost bands).  
- Detect outliers (e.g., negative costs, implausible durations).  
- Assign default confidence to human-verified fields.  
**Files:**  
- `/etl/pipelines/normalize/validators.py`  
- `/etl/pipelines/normalize/normalizer.py`  
- `/etl/utils/validation_rules.py`
**Status:** Complete

### 1.6 Data Publishing
**Goal:** Load validated data into Postgres and NewSearch.  
**Tasks:**  
- Create table insert/upsert logic for each schema (schools, programs, pricing).  
- Generate NewSearch-compatible JSON documents.  
- Bulk-load records and verify counts.  
- Build error logging for rejected records.  
**Files:**  
- `/etl/pipelines/publish/postgres_writer.py`  
- `/etl/pipelines/publish/Newsearch_indexer.py`  
- `/etl/configs/db_config.yaml`  
**Status:** New  

### 1.7 Manifest & Snapshot Management
**Goal:** Create manifest JSON for reproducibility.  
**Tasks:**  
- Generate per-source, per-school record counts.  
- Record extraction timestamp and hash digests.  
- Write manifest to S3 under `snapshots/manifest_{id}.json`.  
- Validate manifest schema and sign with checksum.  
**Files:**  
- `/etl/utils/snapshot_manager.py`  
- `/etl/output/manifest_2025Q1-MVP.json`  
**Status:** New  

## 2. Backend & API

### 2.1 Database Schema
**Goal:** Define schema using Drizzle ORM.
**Tasks:**
- Implement `schools`, `campuses`, `programs`, `pricing`, and `attributes` tables.
- Configure foreign keys and indexes for geo queries.
- Run Drizzle migration script and verify schema in RDS.
- Commit generated SQL migrations.
**Files:**
- `/apps/web/drizzle/schema.ts`
- `/apps/web/drizzle/migrations/0001_init.sql`
- `/apps/web/drizzle.config.ts`
**Status:** Awaiting QC

### 2.2 DB Connection Layer
**Goal:** Create type-safe Postgres connection utilities.
**Tasks:**
- Initialize Drizzle client.
- Add connection pooling for RDS.
- Expose read/write helpers for API routes.
- Unit test query results with sample data.
**Files:**
- `/apps/web/lib/db.ts`
- `/apps/web/lib/types.ts`
**Status:** Complete

### 2.3 NewSearch Client
**Goal:** Implement search interface for APIs.
**Tasks:**
- Configure NewSearch SDK and credentials.
- Build helper for geo + filter queries.
- Add pagination and sorting functions.
- Test index health and mapping consistency.
**Files:**
- `/apps/web/lib/Newsearch.ts`
- `/apps/web/lib/search_utils.ts`
**Status:** Complete

### 2.4 API Routes — Schools
**Goal:** Serve searchable list and detail endpoints.
**Tasks:**
- Implement `GET /api/schools` with filters and pagination.
- Implement `GET /api/schools/[id]` for profile data.
- Add response caching headers.
- Validate outputs with Zod schema.
**Files:**
- `/apps/web/app/api/schools/route.ts`
- `/apps/web/app/api/schools/[id]/route.ts`
**Status:** Complete  

### 2.5 API Routes — Metadata
**Goal:** Serve manifest and snapshot metadata.  
**Tasks:**  
- Create `GET /api/meta` returning snapshot_id, as_of, and coverage stats.  
- Include total school count and last ETL run date.  
- Cache result in Redis (optional).  
**Files:**  
- `/apps/web/app/api/meta/route.ts`  
**Status:** New  

## 3. Frontend (Next.js)

### 3.1 Layout & Navigation
**Goal:** Implement base layout and shared navigation.
**Tasks:**
- Add `NavBar`, `Footer`, and responsive layout container.
- Configure metadata for SEO (title, description).
- Add favicon, logo, and placeholder theme.
**Files:**
- `/apps/web/app/layout.tsx`
- `/apps/web/app/page.tsx`
- `/apps/web/components/NavBar.tsx`
- `/apps/web/components/Footer.tsx`
**Status:** Complete  

### 3.2 Search & Filters UI
**Goal:** Build interactive search and filters.  
**Tasks:**  
- Implement `SearchBar` with location autocomplete.  
- Add filters: cost range, training type, VA eligibility.  
- Wire up NewSearch queries with React Query.  
- Display count and sorting options.  
**Files:**  
- `/apps/web/app/search/page.tsx`  
- `/apps/web/components/SearchBar.tsx`  
- `/apps/web/components/FilterPanel.tsx`  
- `/apps/web/hooks/useSearch.ts`  
**Status:** New  

### 3.3 School Compare Cards
**Goal:** Render normalized data in list view.  
**Tasks:**  
- Build responsive card layout.  
- Display cost band, rating, part type, and location.  
- Include “as-of” tooltip and source icon.  
- Add hover and compare interactions.  
**Files:**  
- `/apps/web/components/SchoolCard.tsx`  
- `/apps/web/components/TrustBadge.tsx`  
**Status:** New  

### 3.4 School Profile Page
**Goal:** Show full details for a single school.  
**Tasks:**  
- Fetch data from `/api/schools/[id]`.  
- Render programs, fleet, and timeline details.  
- Integrate Mapbox map with campus markers.  
- Add provenance panel showing confidence and timestamps.  
**Files:**  
- `/apps/web/app/schools/[id]/page.tsx`  
- `/apps/web/components/SchoolDetails.tsx`  
- `/apps/web/components/ProvenancePanel.tsx`  
- `/apps/web/components/MapView.tsx`  
**Status:** New  

### 3.5 “Suggest an Edit” Feedback Form
**Goal:** Allow users to propose corrections.  
**Tasks:**  
- Build form with field suggestions and contact optional.  
- Submit to `/api/feedback` storing payload in S3 JSON.  
- Add success/failure toast notifications.  
**Files:**  
- `/apps/web/components/SuggestEditForm.tsx`  
- `/apps/web/app/api/feedback/route.ts`  
**Status:** New  

### 3.6 Global Styling & Components
**Goal:** Configure Tailwind, shadcn, and typography.  
**Tasks:**  
- Initialize Tailwind config with custom theme.  
- Generate base components (`Button`, `Card`, `Badge`).  
- Import typography and color palette.  
- Set global dark/light modes.  
**Files:**  
- `/apps/web/tailwind.config.ts`  
- `/apps/web/styles/globals.css`  
- `/apps/web/components/ui/*`  
**Status:** New  

## 4. Infrastructure & DevOps

### 4.1 Terraform Setup
**Goal:** Provision core AWS infra.
**Tasks:**
- Define modules for EC2, RDS, S3, NewSearch, CloudFront.
- Configure VPC networking and security groups.
- Apply terraform plan in staging.
- Document outputs (hostnames, endpoints).
**Files:**
- `/infra/terraform/main.tf`
- `/infra/terraform/modules/*`
- `/infra/terraform/variables.tf`
**Status:** Complete (Agent: Pink)
**Completion Notes:**
- Adapted Terraform for existing EC2/RDS infrastructure
- Created OpenSearch Service module for search functionality
- Created S3 buckets module for data storage pipeline
- Created Route53 module for DNS configuration
- Provided comprehensive README with usage instructions

### 4.2 CI/CD Configuration
**Goal:** Automate test, build, and deploy.
**Tasks:**
- Create GitHub Actions for lint/test/build.
- Add deploy job to push Docker image to ECR.
- Trigger ECS/EC2 deploy via Terraform outputs.
- Notify on completion via Slack webhook.
**Files:**
- `/.github/workflows/build.yml`
- `/.github/workflows/deploy.yml`
**Status:** Complete  

### 4.3 Dockerization
**Goal:** Build containers for ETL and web apps.  
**Tasks:**  
- Write multi-stage Dockerfiles for small image size.  
- Add health checks and entrypoints.  
- Test local compose build for both services.  
**Files:**  
- `/apps/web/Dockerfile`  
- `/etl/Dockerfile`  
- `/infra/docker-compose.prod.yml`  
**Status:** New  

### 4.4 Monitoring & Logging
**Goal:** Enable log and metric collection.  
**Tasks:**  
- Add CloudWatch groups for EC2 and ETL logs.  
- Integrate Sentry DSN with frontend and backend.  
- Create dashboards for crawl volume and ETL success.  
**Files:**  
- `/apps/web/lib/logger.ts`  
- `/etl/utils/logger.py`  
- `/infra/terraform/monitoring.tf`  
**Status:** New  

### 4.5 Backup & Snapshot Automation
**Goal:** Automate data backup policies.  
**Tasks:**  
- Enable daily RDS snapshots.  
- Configure S3 lifecycle policies for infrequent access.  
- Write cron-based snapshot verifier script.  
**Files:**  
- `/infra/terraform/backups.tf`  
- `/infra/scripts/create_snapshot.sh`  
**Status:** New  

## 5. QA & Documentation

### 5.1 Test Harness
**Goal:** Validate ETL and API correctness.  
**Tasks:**  
- Unit test LLM extraction and normalization.  
- API tests for `/schools` and `/meta` endpoints.  
- Snapshot test for rendered compare cards.  
**Files:**  
- `/etl/tests/test_extractors.py`  
- `/apps/web/tests/api.test.ts`  
- `/apps/web/tests/components.test.tsx`  
**Status:** New  

### 5.2 Coverage & Confidence Report
**Goal:** Measure ETL completeness.  
**Tasks:**  
- Compute % schools with populated core fields.  
- Aggregate mean confidence scores per field.  
- Output coverage JSON summary.  
**Files:**  
- `/etl/reports/coverage_report.py`  
- `/etl/output/coverage_summary_2025Q1-MVP.json`  
**Status:** New  

### 5.3 Developer Documentation
**Goal:** Document local setup and workflows.  
**Tasks:**  
- Write onboarding guide and architecture overview.  
- Document how to run ETL locally and redeploy app.  
- Add example `.env` configuration for staging.  
**Files:**  
- `/docs/DEVELOPMENT.md`  
- `/docs/ETL_RUNBOOK.md`  
- `/docs/DEPLOYMENT.md`  
**Status:** New  

## 6. Schema & Data Definition

| Task | Purpose | Example Subtasks | Files | Status |
|------|----------|------------------|--------|--------|
| **Define School schema** | Core entity (name, location, contact) | Define Pydantic + Zod models, validate deduping, seed 10 examples | `/etl/schemas/school_schema.py`, `/apps/web/drizzle/schema.ts` | Status: Complete |
| **Define Program schema** | Program types, hours, duration | Map PPL/IR/CPL/CFI enums, add typical hour bands | same as above | Status: Complete |
| **Define Pricing schema** | Normalized rate + cost data | Add min/max totals, rate assumptions, inclusions | same as above | Status: Complete |
| **Define Metrics schema** | Reliability data (placeholder) | Define training_velocity, cancellation_rate | same as above | Status: Complete |
| **Define Attributes schema** | Semi-structured tags | Create flexible JSONB column for "other" data | same as above | Status: Complete |

## 7. Release & Handoff

### 7.1 MVP Dry Run
**Goal:** Validate full ETL → publish → front-end pipeline.  
**Tasks:**  
- Execute `run_etl.py` and record metrics.  
- Load output into RDS + NewSearch.  
- Deploy web build to EC2 staging.  
- Confirm search and detail pages functional.  
**Files:**  
- `/etl/run_etl.py`  
- `/apps/web/.env`  
**Status:** New  

### 7.2 QA + Signoff
**Goal:** Verify performance and data accuracy.  
**Tasks:**  
- Run automated tests.  
- Review 20 random school profiles manually.  
- Check data provenance display.  
**Files:**  
- `/docs/QA_CHECKLIST.md`  
- `/etl/reports/coverage_summary_2025Q1-MVP.json`  
**Status:** New  

### 7.3 Production Deployment
**Goal:** Deploy MVP snapshot to production.  
**Tasks:**  
- Apply Terraform changes.  
- Deploy latest Docker images to EC2.  
- Update snapshot manifest in S3.  
- Validate DNS + SSL via CloudFront.  
**Files:**  
- `/infra/terraform/outputs.tf`  
- `/apps/web/Dockerfile`  
- `/etl/run_etl.py`  
**Status:** New  

---

**End of Document — WheelsUp MVP Task List (v1.0)**
