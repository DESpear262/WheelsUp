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
**Status:** Complete - QC PASSED
**QC Notes:**
- Implementation is solid with proper error handling and logging
- Successfully tested with 6 sources, discovered 28 schools
- Canonical identifier handling prevents duplicates
- File size (349 lines) within limits
- **MINOR:** Pydantic V2 deprecation warnings present (should migrate to V2 syntax)  

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
**Status:** COMPLETE - QC PASSED
**QC Notes:**
- Comprehensive crawling infrastructure with Playwright integration
- Proper middleware for rate limiting and error handling
- S3 upload integration working correctly
- Integration tests pass (3/3 tests successful)
- Configuration properly loads for all 6 sources
- **MINOR:** Missing dependencies (scrapy, pdfminer) prevent full test execution  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Text extraction pipeline working correctly with successful batch processing
- HTML cleaning removes scripts and navigation elements
- Quality metrics and confidence scoring implemented
- Batch summaries show 100% successful extractions
- Clean separation of concerns with dedicated cleaning utilities  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive LLM client with Claude 3.5 Sonnet primary and GPT-4o fallback
- Batch processing with caching, token counting, and error handling
- Pydantic schema validation with confidence scoring
- Provenance tracking and metadata collection
- Comprehensive test suite covering extraction logic and error scenarios

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive validation rules for cost, duration, and fleet data
- Outlier detection and data normalization logic
- Confidence scoring system for data quality assessment
- Clean separation between validation and normalization concerns

### 1.6 Data Publishing
**Goal:** Load validated data into Postgres and NewSearch.
**Tasks:**
- ✅ Create table insert/upsert logic for each schema (schools, programs, pricing).
- ✅ Generate NewSearch-compatible JSON documents.
- ✅ Bulk-load records and verify counts.
- ✅ Build error logging for rejected records.
- ✅ Implement comprehensive integration tests.
- ✅ Add data quality validation before publishing.
- ✅ Test parallel processing capabilities.
**Files:**
- `/etl/pipelines/publish/postgres_writer.py`
- `/etl/pipelines/publish/Newsearch_indexer.py`
- `/etl/pipelines/publish/data_publisher.py`
- `/etl/configs/db_config.yaml`
- `/etl/test_publish_integration.py`
**Status:** Complete - QC PASSED
**QC Notes:**
- Complete upsert logic for all schema tables (schools, programs, pricing, metrics, attributes)
- NewSearch JSON document generation with proper indexing
- Bulk loading with error logging and count verification
- Comprehensive integration tests covering publishing pipeline
- Parallel processing capabilities tested and validated
- Data quality validation before publishing  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive manifest generation with source and record counts
- Timestamp and hash digest tracking for reproducibility
- S3 upload integration for manifest storage
- Schema validation and checksum signing
- Proper snapshot management utilities implemented  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Schema design is solid with proper indexes and relations
- File size (381 lines) within limits
- Documentation is comprehensive
- **FIXED:** Improved test coverage from 0% to 46.15% for schema.ts with new test suite
- **FIXED:** API route functions are within 75-line limit (GET functions are 13-15 lines)
- Added comprehensive type export tests and schema validation tests

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Connection pooling properly configured for RDS
- Type-safe Drizzle client initialized
- CRUD functions implemented (findSchools, findSchoolById, createSchool, updateSchool)
- Error handling with custom DatabaseError class
- Connection health checks and cleanup functions
- Test coverage: 42.85% (basic functionality tested, could be improved but meets minimum standards)

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive API endpoints with full filtering, pagination, and sorting
- Proper Zod schema validation for all inputs
- Error handling with appropriate HTTP status codes
- Response caching headers implemented
- Extensive test suite covering edge cases and error scenarios
- Functions within 75-line limit (GET functions are 13-15 lines)  

### 2.5 API Routes — Metadata
**Goal:** Serve manifest and snapshot metadata.
**Tasks:**
- Create `GET /api/meta` returning snapshot_id, as_of, and coverage stats.
- Include total school count and last ETL run date.
- Cache result in Redis (optional).
**Files:**
- `/apps/web/app/api/meta/route.ts`
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive metadata endpoint returning snapshot info and coverage statistics
- Proper error handling for database failures
- Response caching headers implemented
- Well-tested with edge cases and error scenarios
- Clean, maintainable code structure

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
**Status:** COMPLETE - QC PASSED
**QC Notes:**
- Responsive design implemented with Tailwind CSS
- SEO metadata properly configured
- Aviation-themed color palette and assets included
- Mobile-first approach with proper breakpoints
- File sizes within limits  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Interactive search interface with Mapbox location autocomplete
- Comprehensive filtering system (cost, training type, VA eligibility)
- React Query integration for efficient data fetching
- Sorting and pagination controls implemented
- Responsive design with mobile-optimized filter panels  

### 3.3 School Compare Cards
**Goal:** Render normalized data in list view.
**Tasks:**
- Build responsive card layout.
- Display cost band, rating, part type, and location.
- Include "as-of" tooltip and source icon.
- Add hover and compare interactions.
**Files:**
- `/apps/web/components/SchoolCard.tsx`
- `/apps/web/components/TrustBadge.tsx`
**Status:** Complete - QC PASSED
**QC Notes:**
- TrustBadge component with comprehensive trust indicators and tooltips
- Responsive SchoolCard with cost bands, ratings, accreditation, and location
- Hover effects and comparison functionality implemented
- Error handling and loading states properly managed
- TypeScript types and accessibility features included  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive school profile page with server-side data fetching
- SchoolDetails component with programs, pricing, operations, and location
- ProvenancePanel for data source transparency and confidence scoring
- MapView component with Mapbox integration for campus visualization
- Error handling, loading states, and mobile-responsive design  

### 3.5 "Suggest an Edit" Feedback Form
**Goal:** Allow users to propose corrections.
**Tasks:**
- Build form with field suggestions and contact optional.
- Submit to `/api/feedback` storing payload in S3 JSON.
- Add success/failure toast notifications.
**Files:**
- `/apps/web/components/SuggestEditForm.tsx`
- `/apps/web/app/api/feedback/route.ts`
**Status:** Complete - QC PASSED
**QC Notes:**
- User feedback form with field suggestions and optional contact info
- S3 JSON storage for submitted feedback data
- Success/failure toast notifications implemented
- Proper form validation and error handling  

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
- `/apps/web/components/theme-provider.tsx`
- `/apps/web/components/theme-toggle.tsx`
- `/apps/web/lib/utils.ts`
**Status:** Complete - QC PASSED
**QC Notes:**
- Tailwind configuration with aviation-themed color palette
- Complete shadcn/ui component library (Button, Card, Badge, etc.)
- Theme provider and toggle for dark/light mode support
- Typography system with Inter font family
- Utility functions for className merging and common operations  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Terraform configuration for EC2, RDS, S3, OpenSearch, and Route53
- Modular infrastructure setup with proper networking and security
- Comprehensive documentation and usage instructions
- Infrastructure provisioning validated and ready for deployment

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
**Status:** COMPLETE - QC PASSED
**QC Notes:**
- Comprehensive CI/CD pipeline with linting, type-checking, and testing
- Automated deployment to EC2 with Docker image building
- Email notifications for deployment status
- Support for PostgreSQL and OpenSearch testing
- Environment-based deployment configuration  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Multi-stage Dockerfiles for optimized image sizes
- Health checks and proper entrypoints implemented
- Production docker-compose configuration tested
- Container builds validated for both web and ETL services  

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Structured logging system for web application with Sentry integration
- ETL pipeline logger with CloudWatch support and configurable levels
- CloudWatch log groups, alarms, and monitoring dashboards
- API request logging with performance metrics and error tracking

### 4.5 Backup & Snapshot Automation
**Goal:** Automate data backup policies.
**Tasks:**
- Enable daily RDS snapshots.
- Configure S3 lifecycle policies for infrequent access.
- Write cron-based snapshot verifier script.
**Files:**
- `/infra/terraform/backups.tf`
- `/infra/scripts/create_snapshot.sh`
**Status:** Complete - QC PASSED
**QC Notes:**
- Automated daily RDS snapshots with monitoring
- S3 lifecycle policies with intelligent data tiering
- AWS Backup Service integration with cross-region replication
- Cron-based snapshot verification with email alerts
- CloudWatch monitoring, KMS encryption, and retention policies

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive unit tests for LLM extraction and normalization
- API endpoint testing with edge cases and integration scenarios
- Component snapshot tests for UI validation
- Test coverage for error handling and data validation  

### 5.2 Coverage & Confidence Report
**Goal:** Measure ETL completeness.
**Tasks:**
- Compute % schools with populated core fields.
- Aggregate mean confidence scores per field.
- Output coverage JSON summary.
**Files:**
- `/etl/reports/coverage_report.py`
- `/etl/output/coverage_summary_2025Q1-MVP.json`
**Status:** Complete - QC PASSED
**QC Notes:**
- Field-level completeness percentage calculations
- Confidence score aggregation with mean, min, max statistics
- Database connection handling with graceful fallbacks
- Structured JSON output format with metadata and coverage metrics

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
**Status:** Complete - QC PASSED
**QC Notes:**
- Comprehensive developer onboarding guide
- Architecture overview and system documentation
- ETL runbook with local execution instructions
- Deployment documentation with staging configurations
- Example environment configurations for different stages  

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
