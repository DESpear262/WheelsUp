# System Architecture & Patterns

## Project Overview
WheelsUp is a flight school marketplace MVP that aggregates, normalizes, and presents flight school data to help students compare training options.

## Architecture Overview
- **Frontend**: Next.js 15.0.3 with TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Node.js 22 LTS API routes
- **Database**: PostgreSQL 16 with PostGIS 3.4 for spatial queries
- **Search**: Amazon OpenSearch Service 2.13 for faceted search
- **ETL Pipeline**: Python 3.14 with Scrapy/Playwright for data acquisition, LLM extraction
- **Infrastructure**: AWS (EC2, RDS, OpenSearch, S3, VPC)

## Key Components
1. **Data Acquisition Layer**: Crawls flight school data from public sources
2. **ETL Pipeline**: Extracts, validates, and normalizes data using LLM schema extraction
3. **Web Application**: Searchable interface with filters, maps, and comparison tools
4. **Data Storage**: Relational (Postgres) + Search (OpenSearch) with full provenance tracking

## Design Patterns
- **Snapshot-based ETL**: Each full pipeline run creates an immutable data snapshot
- **Provenance tracking**: Every data field includes source, timestamp, and confidence
- **Multi-source aggregation**: Combines data from websites, directories, and user-generated content
- **LLM-powered extraction**: Uses Claude 3.5 Sonnet for structured data extraction from unstructured text

## Current State
- Project in early setup phase
- No codebase implemented yet
- Architecture defined in PRD but not yet built
