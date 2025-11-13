# File Index - WheelsUp Flight School Marketplace

This index documents all files created during development, organized by functionality.

## ETL Pipeline Files

### Source Discovery Pipeline (`etl/pipelines/discover/`)

| File | Description | Purpose |
|------|-------------|---------|
| `__init__.py` | Package initialization | Marks directory as Python package for source discovery pipeline |
| `seed_sources.py` | Source discovery and seeding script | Reads sources.yaml config and generates seed URLs with canonical identifiers for flight school discovery |

### Crawling Pipeline (`etl/pipelines/crawl/`)

| File | Description | Purpose |
|------|-------------|---------|
| `run_spiders.py` | Main crawler orchestrator | Coordinates spider execution with seed discovery integration and crawl method selection |
| `middleware.py` | Custom Scrapy middleware | Implements retry logic, rate limiting, and enhanced logging for flight school crawling |
| `playwright_handler.py` | Playwright integration | Existing handler for JavaScript-heavy websites requiring browser automation |
| `base_spider.py` | Base spider class | Enhanced with seed URL support, S3 upload integration, and configurable crawling |
| `spiders/*.py` | Individual spider implementations | Scrapy spiders for specific flight school directories (FAA, AOPA, etc.) |

### Publishing Pipeline (`etl/pipelines/publish/`)

| File | Description | Purpose |
|------|-------------|---------|
| `data_publisher.py` | Main publishing orchestrator | Coordinates bulk loading to PostgreSQL and OpenSearch with error handling and validation |
| `postgres_writer.py` | PostgreSQL data writer | Implements upsert logic for schools, programs, and pricing tables with conflict resolution |
| `newsearch_indexer.py` | OpenSearch document indexer | Creates search-optimized JSON documents and manages bulk indexing operations |
| `__init__.py` | Package initialization | Marks directory as Python package for data publishing pipeline |

### Configuration Files (`etl/configs/`)

| File | Description | Purpose |
|------|-------------|---------|
| `sources.yaml` | Flight school directory sources | Configuration for all flight school data sources with crawling parameters |
| `crawl_settings.yaml` | Crawling pipeline settings | Comprehensive settings for crawling behavior, middleware, and S3 upload configuration |
| `db_config.yaml` | Database publishing settings | PostgreSQL and OpenSearch connection settings, publishing options, and mock configurations |

### Output Files (`etl/output/`)

| File Pattern | Description | Purpose |
|--------------|-------------|---------|
| `seed_discovery_*.json` | Individual source discovery results | Contains discovered schools, canonical identifiers, and metadata for each configured source |
| `seed_discovery_summary_*.json` | Batch discovery summary | Aggregates results across all sources with statistics and duplicate analysis |

### Reports (`etl/reports/`)

| File | Description | Purpose |
|------|-------------|---------|
| `coverage_report.py` | Coverage and confidence analysis | Generates comprehensive data quality reports for ETL pipeline completeness |

### Test Files (`etl/`)

| File | Description | Purpose |
|------|-------------|---------|
| `test_pipeline.py` | ETL pipeline integration tests | Validates end-to-end ETL pipeline functionality |
| `test_extraction.py` | Text extraction tests | Tests HTML/PDF text extraction capabilities |
| `test_data_publish.py` | Data publishing tests | Tests PostgreSQL and OpenSearch publishing with mock implementations |
| `test_coverage_report.py` | Coverage report tests | Validates coverage analysis functionality with mocked database |

### Output Files (`etl/output/`)

| File Pattern | Description | Purpose |
|--------------|-------------|---------|
| `coverage_summary_*.json` | Coverage and confidence reports | JSON summaries of ETL pipeline data completeness and quality metrics |

## Web Application Files

### API Routes (`apps/web/app/api/`)

| File | Description | Purpose |
|------|-------------|---------|
| `schools/route.ts` | Schools list API endpoint | GET /api/schools with filtering, pagination, and search capabilities |
| `schools/[id]/route.ts` | School detail API endpoint | GET /api/schools/[id] with comprehensive school information and related data |
| `meta/route.ts` | System metadata API endpoint | GET /api/meta providing snapshot information, coverage statistics, and system health |

### Landing Page (`apps/web/app/`)

| File | Description | Purpose |
|------|-------------|---------|
| `page.tsx` | Marketing landing page with hero and sidebar feature tabs | Presents core value props with CTA, trust metrics, and compact sidebar icons so the feature visuals no longer dominate the viewport |

### Build Tooling (`apps/web/`)

| File | Description | Purpose |
|------|-------------|---------|
| `postcss.config.js` | PostCSS configuration for Tailwind compilation | Registers Tailwind CSS and Autoprefixer so utility classes and `@apply` directives build correctly |
| `tailwind.config.ts` | Tailwind CSS theme configuration | Provides aviation-themed palette, spacing, and animation settings with ESM export compatible with Next.js 15/turbopack |

### Database Layer (`apps/web/lib/`)

| File | Description | Purpose |
|------|-------------|---------|
| `db.ts` | Database connection utilities | Drizzle ORM client with connection pooling and query helpers |
| `logger.ts` | Structured logging system | Comprehensive logging with Sentry integration, API request tracking, and performance monitoring |

### Logging and Monitoring (`etl/utils/`)

| File | Description | Purpose |
|------|-------------|---------|
| `logger.py` | ETL pipeline logger | Structured logging for ETL operations with CloudWatch integration and configurable levels |

### Infrastructure Monitoring (`infra/terraform/`)

| File | Description | Purpose |
|------|-------------|---------|
| `monitoring.tf` | CloudWatch monitoring setup | Log groups, alarms, dashboards, and IAM policies for comprehensive AWS monitoring |

### Local Infrastructure Support (`infra/docker/`)

| File | Description | Purpose |
|------|-------------|---------|
| `postgres/init.sql` | PostgreSQL bootstrap script | Creates the `wheelsup_dev` database, `wheelsup_user`, PostGIS extensions, and grants needed for local development |

### Test Files (`etl/`)

| File | Description | Purpose |
|------|-------------|---------|
| `test_crawl_integration.py` | Crawling pipeline integration tests | Validates configuration loading, seed discovery integration, and crawl method detection |
| `test_data_publish.py` | Data publishing pipeline tests | Tests database configuration, data structures, publisher initialization, and validation logic |

## Key Features Implemented

### Canonical Identifiers
- **Domain**: Primary identifier extracted from URLs for deduplication
- **Phone**: Formatted phone numbers for contact verification
- **ICAO Code**: Aviation-specific airport/facility identifiers

### Data Structures
- `SeedDiscoveryResult`: Structured result class with JSON serialization
- Duplicate detection and logging for data quality analysis
- Timestamped discovery records with confidence scores
- `FlightSchoolCrawlerProcess`: Main crawler orchestrator with seed integration
- Custom Scrapy middleware for retry logic and rate limiting
- `DataPublisher`: Orchestrator for bulk loading to PostgreSQL and OpenSearch
- `PostgresWriter`: Upsert logic with conflict resolution by confidence scores
- `NewSearchIndexer`: Search-optimized document generation for OpenSearch

### Integration Points
- Reads from `etl/configs/sources.yaml`, `crawl_settings.yaml`, and `db_config.yaml`
- Outputs to `etl/output/` directory following existing patterns
- Compatible with existing ETL pipeline structure and logging
- S3 upload integration with snapshot-based organization
- Playwright support for JavaScript-heavy sources
- Seed discovery integration for targeted crawling
- Parallel processing for PostgreSQL and OpenSearch publishing
- Configurable data validation and error handling

### Testing Results
#### Source Discovery Pipeline
- ✅ Successfully processed 6 configured sources
- ✅ Discovered 28 sample schools across different source types
- ✅ Generated structured JSON output with canonical identifiers
- ✅ No linter errors or import issues
- ✅ Follows codebase patterns from text extraction pipeline

#### Crawling Pipeline
- ✅ All 3/3 integration tests passed
- ✅ Configuration loading validated for sources.yaml and crawl_settings.yaml
- ✅ Crawl method detection working correctly (scrapy vs playwright)
- ✅ Seed discovery file structure validation successful

#### Data Publishing Pipeline
- ✅ All 4/4 integration tests passed
- ✅ Database configuration loading validated
- ✅ Data structures and Pydantic schemas working correctly
- ✅ Publisher initialization with mock mode functional
- ✅ Data validation logic implemented and tested
- ✅ Optional database dependencies handled gracefully
- ✅ Bulk loading and error logging framework ready
