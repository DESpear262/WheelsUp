# Project Brief

## Project Name
WheelsUp - Flight School Marketplace MVP

## Vision
WheelsUp aims to become the authoritative, student-first marketplace for flight training — the *Zillow of flight schools* — by aggregating, normalizing, and verifying opaque flight school data.

## Objective
Deliver a fully functional, reproducible data and web stack that enables:
- End users (students) to search, filter, and compare flight schools
- The product and engineering team to run a complete scrape → ETL → publish cycle
- Each displayed data field to show **provenance, freshness, and confidence**

## Scope (MVP)
**In Scope:**
- Crawl public flight school data from directories, websites, and metadata sources
- Single-run ETL pipeline for extraction, validation, normalization using LLM
- Searchable web UI with filters, map view, and comparison tools
- AWS EC2-hosted stack with Postgres, OpenSearch, and Next.js frontend
- Complete data transparency with provenance tracking

**Out of Scope:**
- Continuous crawl or automatic data refresh
- Partner data integration
- AI concierge or guided comparison features
- Lead routing, CRM, or payment systems
- Serverless deployment

## Success Criteria
- ≥ 1,000 U.S. flight schools indexed
- ≥ 70% completeness on cost and duration fields
- ≥ 0.8 mean field confidence from LLM extraction
- 100% ETL pipeline reliability
- < 2.5s search page load time (p95)
- 100% data fields show "as-of" timestamps

## Technical Foundation
- **Frontend**: Next.js 15.0.3 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Node.js 22 LTS API routes with Drizzle ORM
- **Database**: PostgreSQL 16 + PostGIS + Amazon OpenSearch Service
- **ETL**: Python 3.14 + Scrapy/Playwright + Claude 3.5 Sonnet for LLM extraction
- **Infrastructure**: AWS (EC2, RDS, S3, VPC, CloudFront)

## Key Innovation
- **LLM-powered schema extraction** from unstructured web content
- **Snapshot-based immutable data versioning** for auditability
- **Complete data provenance tracking** (source, timestamp, confidence)
- **Multi-source data aggregation** with deduplication

## Timeline
8-12 weeks for full MVP delivery, with Phase 0 (setup) currently complete.
